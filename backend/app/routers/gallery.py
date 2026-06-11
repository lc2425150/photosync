"""
PhotoSync — photo gallery & thumbnail router.
"""

from __future__ import annotations

import hashlib
import os

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncFile
from app.schemas import GalleryResponse, GalleryPhoto
from app.exceptions import FileNotFoundError_, as_http_exception
from app.config import settings
from app.services.thumbnail import generate_thumbnail

router = APIRouter(prefix="/api/v1/gallery", tags=["gallery"])


@router.get("", response_model=GalleryResponse)
async def list_photos(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(
        select(func.count()).where(SyncFile.status == "synced")
    ) or 0
    r = await db.execute(
        select(SyncFile)
        .where(SyncFile.status == "synced")
        .order_by(SyncFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = []
    for f in r.scalars().all():
        items.append(GalleryPhoto(
            id=f.id,
            filename=f.filename,
            file_size=f.file_size,
            dest_path=f.dest_path,
            created_at=str(f.created_at),
            thumbnail_url=f"/api/v1/gallery/{f.id}/thumbnail",
            image_url=f"/api/v1/gallery/{f.id}/image",
        ))
    return GalleryResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{fid:int}/thumbnail")
async def get_thumbnail(fid: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(SyncFile, fid)
    if not f or not f.dest_path or not os.path.exists(f.dest_path):
        raise as_http_exception(FileNotFoundError_())
    thumb_name = hashlib.sha256(f.dest_path.encode()).hexdigest()[:16] + ".jpg"
    thumb_path = os.path.join(settings.thumbnail_dir, thumb_name)
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path, media_type="image/jpeg")
    result = await generate_thumbnail(f.dest_path, settings.thumbnail_dir)
    if result:
        return FileResponse(result, media_type="image/jpeg")
    raise as_http_exception(FileNotFoundError_())


@router.get("/{fid:int}/image")
async def get_image(fid: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(SyncFile, fid)
    if not f or not f.dest_path or not os.path.exists(f.dest_path):
        raise as_http_exception(FileNotFoundError_())
    return FileResponse(f.dest_path)
