"""
PhotoSync — sync history router.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncHistory, SyncFile
from app.schemas import HistoryResponse, HistoryDetailResponse, SyncFileResponse, PaginatedResponse

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("", response_model=PaginatedResponse)
async def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    profile_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(SyncHistory)
    if status:
        q = q.where(SyncHistory.status == status)
    if profile_id is not None:
        q = q.where(SyncHistory.profile_id == profile_id)
    q = q.order_by(SyncHistory.started_at.desc())

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    r = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = [HistoryResponse.model_validate(h) for h in r.scalars().all()]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{hid:int}", response_model=HistoryDetailResponse)
async def get_history(hid: int, db: AsyncSession = Depends(get_db)):
    h = await db.get(SyncHistory, hid)
    if not h:
        from app.exceptions import NotFoundError, as_http_exception
        raise as_http_exception(NotFoundError(code="HISTORY_NOT_FOUND", message="同步记录不存在"))
    return HistoryDetailResponse(
        **HistoryResponse.model_validate(h).model_dump(),
        files=[SyncFileResponse.model_validate(f) for f in h.files],
    )


@router.get("/{hid:int}/files", response_model=PaginatedResponse)
async def get_history_files(
    hid: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(SyncFile).where(SyncFile.history_id == hid).order_by(SyncFile.id)
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    r = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = [SyncFileResponse.model_validate(f) for f in r.scalars().all()]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.delete("")
async def clean_history(days: int = Query(90, ge=1), db: AsyncSession = Depends(get_db)):
    from sqlalchemy.sql import func as f2
    cutoff = f2.now().op("-")(f2.make_interval(days))
    await db.execute(delete(SyncHistory).where(SyncHistory.started_at < cutoff))
    await db.commit()
    return {"ok": True}
