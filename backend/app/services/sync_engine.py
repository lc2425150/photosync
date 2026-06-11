"""
PhotoSync — core sync engine.

Handles the full file-sync lifecycle: scan → checksum → dedup →
copy/move → verify → thumbnail → log.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from sqlalchemy import select
from sqlalchemy.sql import func

from app.config import settings
from app.database import async_session
from app.constants import FileSyncStatus, SyncStatus
from app.executors import get_io_executor
from app.models import SyncHistory, SyncFile, SyncProfile
from app.services.checksum import calculate_sha256, verify_checksum
from app.services.dedup import DedupService
from app.services.file_organizer import FileOrganizer
from app.services.file_scanner import scan_files, sanitize_filename, detect_sidecar_files
from app.services.thumbnail import generate_thumbnail
from app.services.ws_manager import ws_manager

logger = logging.getLogger("photosync.sync")

# ── Module-level state (readable via /api/v1/sync/status) ──────────

_is_running: bool = False
_current_progress: dict = {}


def get_progress() -> Optional[dict]:
    return _current_progress if _is_running else None


# ── Engine ──────────────────────────────────────────────────────────

class SyncEngine:
    """Orchestrates a single sync run for a profile + source path pair."""

    def __init__(self, max_workers: int | None = None) -> None:
        self.max_workers = max_workers or settings.max_concurrent_copies
        self._cancel: bool = False

    def cancel(self) -> None:
        self._cancel = True

    # ── Dry run ──────────────────────────────────────────────────

    async def dry_run(self, profile: SyncProfile, source_path: str) -> dict:
        filters = profile.file_filters or {}
        all_files = list(scan_files(source_path, filters))

        async with async_session() as db:
            dedup = DedupService(db)
            new: list[dict] = []
            skipped = 0
            skipped_size = 0
            for fi in all_files:
                try:
                    fh = await calculate_sha256(fi["path"])
                except Exception:
                    skipped += 1
                    skipped_size += fi["size"]
                    continue
                if await dedup.is_duplicate(fh):
                    skipped += 1
                    skipped_size += fi["size"]
                else:
                    new.append({**fi, "hash": fh})

        total_files = len(all_files)
        total_size = sum(f["size"] for f in all_files)
        new_size = sum(f["size"] for f in new)

        return {
            "total_files": total_files,
            "total_size": total_size,
            "new_files": len(new),
            "new_size": new_size,
            "skipped_files": skipped,
            "skipped_size": skipped_size,
            "files": new[:100],  # preview capped at 100
        }

    # ── Full sync ────────────────────────────────────────────────

    async def run_sync(self, profile_id: int, source_path: str) -> int:
        global _is_running, _current_progress
        if _is_running:
            raise RuntimeError("同步引擎正在运行中")

        _is_running = True
        _current_progress = {}
        self._cancel = False

        # Fetch profile
        async with async_session() as sdb:
            profile = await sdb.get(SyncProfile, profile_id)
            if not profile:
                _is_running = False
                raise ValueError(f"Profile {profile_id} not found")

            # Create history record
            org = FileOrganizer(
                profile.destination, profile.sync_mode, profile.custom_template
            )
            h = SyncHistory(
                profile_id=profile.id,
                profile_name=profile.name,
                status=SyncStatus.RUNNING,
                source_path=source_path,
                dest_path=profile.destination,
            )
            sdb.add(h)
            await sdb.commit()
            await sdb.refresh(h)
            history_id = h.id

        # Scan files
        filters = profile.file_filters or {}
        all_files = list(scan_files(source_path, filters))
        total = len(all_files)
        total_bytes = sum(f["size"] for f in all_files)
        _current_progress.update(
            current_file=None, current=0, total=total,
            current_bytes=0, total_bytes=total_bytes,
        )

        await ws_manager.broadcast({
            "type": "sync_started",
            "history_id": history_id,
            "total_files": total,
            "total_bytes": total_bytes,
        })

        start = asyncio.get_event_loop().time()
        sc = sk = fc = 0
        sbytes = 0

        try:
            sem = asyncio.Semaphore(self.max_workers)
            dedup_service = DedupService(None)  # will get fresh db per call

            async def process_one(fi: dict) -> dict:
                nonlocal sbytes
                async with sem:
                    result = {
                        "status": FileSyncStatus.FAILED,
                        "error": None,
                        "dest_path": None,
                        "checksum": None,
                        "size": fi["size"],
                    }
                    try:
                        fh = await calculate_sha256(fi["path"])
                        result["checksum"] = fh

                        # Dedup check (fresh session)
                        async with async_session() as db:
                            ds = DedupService(db)
                            if await ds.is_duplicate(fh):
                                return {**result, "status": FileSyncStatus.SKIPPED,
                                        "error": "已同步过"}

                        dp = org.get_dest_path(fi["name"], fi["mtime"])
                        result["dest_path"] = dp

                        # Copy or move
                        loop = asyncio.get_running_loop()
                        if profile.copy_mode == "move":
                            await loop.run_in_executor(
                                get_io_executor(), self._move, fi["path"], dp
                            )
                        else:
                            await loop.run_in_executor(
                                get_io_executor(), self._copy, fi["path"], dp
                            )

                        # Verify checksum
                        if profile.checksum_verify:
                            if not await verify_checksum(dp, fh):
                                os.remove(dp)
                                return {**result, "status": FileSyncStatus.FAILED,
                                        "error": "校验和不匹配"}

                        # Sidecar files
                        for sc_path in detect_sidecar_files(fi["path"]):
                            sc_dest = os.path.join(
                                os.path.dirname(dp),
                                sanitize_filename(os.path.basename(sc_path)),
                            )
                            await loop.run_in_executor(
                                get_io_executor(), self._copy, sc_path, sc_dest
                            )

                        # Thumbnail (best-effort)
                        try:
                            await generate_thumbnail(dp)
                        except Exception:
                            pass

                        return {**result, "status": FileSyncStatus.SYNCED}
                    except Exception as e:
                        return {**result, "status": FileSyncStatus.FAILED,
                                "error": str(e)}

            # Process files sequentially (each is async but uses semaphore for IO)
            for fi in all_files:
                if self._cancel:
                    break
                _current_progress["current_file"] = fi["name"]
                result = await process_one(fi)

                sbytes += fi["size"]
                _current_progress["current"] += 1
                _current_progress["current_bytes"] = sbytes

                # Write to DB
                async with async_session() as db:
                    sf = SyncFile(
                        history_id=history_id,
                        filename=fi["name"],
                        relative_path=fi.get("relative_path"),
                        source_path=fi["path"],
                        dest_path=result["dest_path"],
                        file_size=fi["size"],
                        checksum=result.get("checksum"),
                        status=result["status"],
                        error_message=result.get("error"),
                    )
                    db.add(sf)

                    if result["status"] == FileSyncStatus.SYNCED:
                        sc += 1
                        ds = DedupService(db)
                        fh = result.get("checksum") or ""
                        if fh:
                            await ds.register_file(fh, fi["path"], fi["size"],
                                                    result["dest_path"] or "")
                    elif result["status"] == FileSyncStatus.SKIPPED:
                        sk += 1
                    else:
                        fc += 1

                    await db.commit()

                # Progress
                elapsed = asyncio.get_event_loop().time() - start
                _current_progress["elapsed_seconds"] = int(elapsed)
                if elapsed > 0 and sbytes > 0:
                    spd = sbytes / elapsed
                    _current_progress["speed_mbps"] = round(spd / 1024 / 1024, 1)
                    remaining = _current_progress["total_bytes"] - sbytes
                    _current_progress["eta_seconds"] = (
                        int(remaining / spd) if spd > 0 else None
                    )

                await ws_manager.broadcast({
                    "type": "sync_progress",
                    **_current_progress,
                })

            # Mark history complete
            async with async_session() as db:
                h = await db.get(SyncHistory, history_id)
                if h:
                    h.status = (
                        SyncStatus.CANCELLED
                        if self._cancel
                        else SyncStatus.COMPLETED
                    )
                    h.synced_files = sc
                    h.skipped_files = sk
                    h.failed_files = fc
                    h.synced_bytes = sbytes
                    h.completed_at = func.now()
                    await db.commit()

            await ws_manager.broadcast({
                "type": "sync_completed",
                "history_id": history_id,
                "status": "cancelled" if self._cancel else "success",
                "synced": sc,
                "skipped": sk,
                "failed": fc,
            })

            return history_id

        finally:
            _is_running = False
            _current_progress = {}

    # ── File helpers (run in executor) ───────────────────────────

    @staticmethod
    def _copy(src: str, dst: str) -> None:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    @staticmethod
    def _move(src: str, dst: str) -> None:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
