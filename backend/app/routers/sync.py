"""
PhotoSync — sync trigger / status / cancel / dry-run / queue router.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncProfile, SyncQueue, QueueStatus
from app.schemas import SyncStatusResponse, DryRunResponse, QueueItemResponse, OkResponse
from app.exceptions import ProfileNotFoundError, QueueNotFoundError, SyncInProgressError, as_http_exception
from app.services.sync_engine import SyncEngine, get_progress

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])

# Singleton — worker.py also creates one; they are independent by design.
_engine = SyncEngine()


@router.post("/trigger", response_model=OkResponse)
async def trigger_sync(
    profile_id: int = Query(...),
    source_path: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    p = await db.get(SyncProfile, profile_id)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    qi = SyncQueue(card_path=source_path, profile_id=profile_id, status=QueueStatus.QUEUED)
    db.add(qi)
    await db.commit()
    return OkResponse()


@router.get("/status", response_model=SyncStatusResponse)
async def sync_status():
    p = get_progress() or {}
    return SyncStatusResponse(
        running=bool(p),
        current_file=p.get("current_file"),
        current=p.get("current", 0),
        total=p.get("total", 0),
        current_bytes=p.get("current_bytes", 0),
        total_bytes=p.get("total_bytes", 0),
        speed_mbps=p.get("speed_mbps"),
        eta_seconds=p.get("eta_seconds"),
        elapsed_seconds=p.get("elapsed_seconds", 0),
    )


@router.post("/cancel", response_model=OkResponse)
async def cancel_sync():
    _engine.cancel()
    return OkResponse()


@router.post("/dry-run", response_model=DryRunResponse)
async def dry_run(
    profile_id: int = Query(...),
    source_path: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    p = await db.get(SyncProfile, profile_id)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    result = await _engine.dry_run(p, source_path)
    return DryRunResponse(**result)


@router.get("/queue", response_model=list[QueueItemResponse])
async def list_queue(db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(SyncQueue).order_by(SyncQueue.queued_at)
    )
    return [QueueItemResponse.model_validate(q) for q in r.scalars().all()]


@router.post("/queue/{qid:int}/cancel", response_model=OkResponse)
async def cancel_queue(qid: int, db: AsyncSession = Depends(get_db)):
    q = await db.get(SyncQueue, qid)
    if not q:
        raise as_http_exception(QueueNotFoundError())
    if q.status == QueueStatus.RUNNING:
        raise as_http_exception(SyncInProgressError())
    q.status = QueueStatus.CANCELLED
    await db.commit()
    return OkResponse()
