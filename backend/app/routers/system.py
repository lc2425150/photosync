"""
PhotoSync — system endpoints: storage, logs, path mapping.
"""

from __future__ import annotations

import shutil
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncLog
from app.schemas import StorageItem, LogEntry, PaginatedResponse
from app.config import settings as app_settings

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/path-mapping")
async def path_mapping():
    """Return the host ↔ container path mapping for the photos mount."""
    return {
        "host_base": app_settings.photos_mount_host_path,
        "container_base": "/photos",
        "description": (
            f"把 NAS 路径 {app_settings.photos_mount_host_path}/xxx "
            f"映射到容器内的 /photos/xxx。设置目标目录时填入 NAS 路径即可。"
        ),
    }


@router.get("/storage", response_model=list[StorageItem])
async def storage():
    result: list[StorageItem] = []
    for path in ["/photos", "/media"]:
        try:
            u = shutil.disk_usage(path)
            result.append(StorageItem(
                path=path,
                total_gb=round(u.total / (1024**3), 1),
                used_gb=round(u.used / (1024**3), 1),
                free_gb=round(u.free / (1024**3), 1),
                usage_percent=round(u.used / u.total * 100, 1),
            ))
        except Exception:
            pass
    return result


@router.get("/logs", response_model=PaginatedResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(SyncLog).order_by(SyncLog.timestamp.desc())
    if level:
        q = q.where(SyncLog.level == level.upper())
    if search:
        q = q.where(SyncLog.message.contains(search))

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    r = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = [
        LogEntry(
            id=l.id,
            level=l.level,
            message=l.message,
            timestamp=str(l.timestamp),
        )
        for l in r.scalars().all()
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
