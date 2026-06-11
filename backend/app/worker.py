"""
PhotoSync — background worker: card detection, sync queue processing,
and periodic cleanup.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, delete
from sqlalchemy.sql import func, text

from app.database import async_session
from app.constants import QueueStatus
from app.models import SyncProfile, SyncQueue, SyncLog, SyncHistory
from app.services.card_detector import CardDetector
from app.services.sync_engine import SyncEngine
from app.services.ws_manager import ws_manager
from app.config import settings

logger = logging.getLogger("photosync.worker")

_running: bool = False


async def start_worker() -> None:
    global _running
    _running = True
    logger.info("Worker 已启动")

    detector = CardDetector(settings.scan_paths, settings.poll_interval)
    engine = SyncEngine(settings.max_concurrent_copies)

    async def on_card_insert(card):
        logger.info("检测到储存卡: %s at %s", card.label, card.path)
        await ws_manager.broadcast({
            "type": "card_inserted",
            "path": card.path,
            "label": card.label,
        })
        async with async_session() as db:
            r = await db.execute(
                select(SyncProfile).where(
                    SyncProfile.enabled == True,
                    SyncProfile.auto_sync == True,
                )
            )
            for p in r.scalars().all():
                if p.match_type == "always" or (
                    p.match_type == "label" and p.match_value == card.label
                ):
                    db.add(SyncQueue(
                        card_path=card.path,
                        card_label=card.label,
                        profile_id=p.id,
                        status=QueueStatus.QUEUED,
                    ))
                    await db.commit()
                    logger.info("已加入队列: %s -> %s", p.name, card.path)
                    await ws_manager.broadcast({"type": "queue_updated"})
                    break

    async def on_card_remove(path: str) -> None:
        await ws_manager.broadcast({"type": "card_removed", "path": path})

    detector.on_insert(on_card_insert)
    detector.on_remove(on_card_remove)

    dt = asyncio.create_task(detector.watch_loop())
    ct = asyncio.create_task(_periodic_cleanup())
    qt = asyncio.create_task(_process_queue(engine))

    try:
        while _running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        for t in (dt, ct, qt):
            t.cancel()


async def stop_worker() -> None:
    global _running
    _running = False
    logger.info("Worker 停止中 ...")


async def _process_queue(engine: SyncEngine) -> None:
    while _running:
        try:
            async with async_session() as db:
                r = await db.execute(
                    select(SyncQueue)
                    .where(SyncQueue.status == QueueStatus.QUEUED)
                    .order_by(SyncQueue.queued_at)
                    .limit(1)
                )
                qi = r.scalar_one_or_none()
                if qi:
                    qi.status = QueueStatus.RUNNING
                    await db.commit()
                    hid = await engine.run_sync(qi.profile_id, qi.card_path)
                    async with async_session() as db2:
                        item = await db2.get(SyncQueue, qi.id)
                        if item:
                            item.status = QueueStatus.COMPLETED
                            item.history_id = hid
                            item.completed_at = func.now()
                            await db2.commit()
                    await ws_manager.broadcast({"type": "queue_updated"})
        except Exception as e:
            logger.error("队列处理错误: %s", e)
        await asyncio.sleep(3)


async def _periodic_cleanup() -> None:
    while _running:
        await asyncio.sleep(3600)
        try:
            async with async_session() as db:
                log_cut = datetime.utcnow() - timedelta(
                    days=settings.log_retention_days
                )
                await db.execute(
                    delete(SyncLog).where(SyncLog.timestamp < log_cut)
                )
                hist_cut = datetime.utcnow() - timedelta(
                    days=settings.history_retention_days
                )
                await db.execute(
                    delete(SyncHistory).where(SyncHistory.started_at < hist_cut)
                )
                await db.commit()
                await db.execute(text("PRAGMA optimize"))
        except Exception as e:
            logger.error("清理错误: %s", e)
