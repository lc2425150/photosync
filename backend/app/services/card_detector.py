"""
PhotoSync — removable storage card detection service.

Only detects actual removable storage cards (SD / CF / USB drives),
not arbitrary mounted paths.  Uses mount-point inspection and
camera-folder heuristics to filter out NAS system volumes.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Callable, Optional

from app.constants import IGNORED_FILES, IGNORED_MOUNT_DIRS


@dataclass
class DetectedCard:
    path: str
    label: str
    total_space: Optional[int] = None
    used_space: Optional[int] = None


# ── Helper utilities ───────────────────────────────────────────────

DCIM_DIRNAME = "DCIM"
MISC_DIRNAME = "MISC"
AVCHD_DIRNAME = "AVCHD"
PRIVATE_DIRNAME = "PRIVATE"

# Camera/card indicator directories (case-insensitive match).
_CARD_INDICATOR_DIRS = frozenset({DCIM_DIRNAME, MISC_DIRNAME, AVCHD_DIRNAME, PRIVATE_DIRNAME})


def _looks_like_storage_card(path: str, label: str) -> bool:
    """Return ``True`` if *path* is likely a removable storage card.

    Heuristics used (in order):
      1. Ignore known NAS system / recycle directories.
      2. Require the path to be a mount point (``os.path.ismount``).
      3. Accept any directory that contains a DCIM folder (strongest
         signal — virtually all cameras create this).
      4. Fall back to checking for other camera indicator dirs
         (MISC / AVCHD / PRIVATE).
    """
    # ── 1. Skip known non-card directories ───────────────────────
    label_lower = label.lower()
    if label_lower in IGNORED_MOUNT_DIRS:
        return False

    # ── 2. Must be a mount point ─────────────────────────────────
    if not os.path.ismount(path):
        return False

    # ── 3. Check for camera indicator directories ────────────────
    try:
        entries = os.listdir(path)
    except PermissionError:
        return False

    for entry in entries:
        if entry.upper() in _CARD_INDICATOR_DIRS:
            ep = os.path.join(path, entry)
            if os.path.isdir(ep):
                return True

    # Not obviously a card — reject.
    return False


def _get_card_space(path: str) -> tuple[Optional[int], Optional[int]]:
    """Return ``(total_bytes, used_bytes)`` or ``(None, None)``."""
    try:
        vfs = os.statvfs(path)
        total = vfs.f_frsize * vfs.f_blocks
        free = vfs.f_frsize * vfs.f_bfree
        return total, total - free
    except Exception:
        return None, None


# ── Detector ───────────────────────────────────────────────────────

class CardDetector:
    """Poll-based card detector.

    Only directories that pass :func:`_looks_like_storage_card` are
    reported as cards.

    Usage:
        detector = CardDetector(["/media", "/mnt"])
        cards = detector.scan()
    """

    def __init__(
        self,
        scan_paths: list[str],
        poll_interval: int = 5,
    ) -> None:
        self.scan_paths = scan_paths
        self.poll_interval = poll_interval
        self._previous_cards: set[str] = set()
        self._on_insert: list[Callable] = []
        self._on_remove: list[Callable] = []

    def on_insert(self, cb: Callable) -> None:
        self._on_insert.append(cb)

    def on_remove(self, cb: Callable) -> None:
        self._on_remove.append(cb)

    def scan(self) -> list[DetectedCard]:
        cards: list[DetectedCard] = []
        for base_path in self.scan_paths:
            if not os.path.isdir(base_path):
                continue
            try:
                for entry in os.listdir(base_path):
                    if entry.lower() in IGNORED_FILES or entry.startswith("."):
                        continue
                    ep = os.path.join(base_path, entry)
                    if not os.path.isdir(ep):
                        continue
                    if not _looks_like_storage_card(ep, entry):
                        continue
                    total, used = _get_card_space(ep)
                    cards.append(
                        DetectedCard(
                            path=ep,
                            label=entry,
                            total_space=total,
                            used_space=used,
                        )
                    )
            except PermissionError:
                continue
        return cards

    async def watch_loop(self) -> None:
        """Continuously poll for card insert/remove events."""
        while True:
            current = {c.path for c in self.scan()}

            for path in current - self._previous_cards:
                card = DetectedCard(path=path, label=os.path.basename(path))
                for cb in self._on_insert:
                    await cb(card)

            for path in self._previous_cards - current:
                for cb in self._on_remove:
                    await cb(path)

            self._previous_cards = current
            await asyncio.sleep(self.poll_interval)
