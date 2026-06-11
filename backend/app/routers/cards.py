"""
PhotoSync — card detection & file preview router.
"""

from __future__ import annotations
from typing import Optional

import os

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncProfile
from app.schemas import CardInfo, FilePreview
from app.exceptions import CardNotFoundError, as_http_exception
from app.services.card_detector import CardDetector
from app.services.file_scanner import scan_files
from app.config import settings

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])


@router.get("", response_model=list[CardInfo])
async def list_cards(db: AsyncSession = Depends(get_db)):
    detected = CardDetector(settings.scan_paths).scan()
    result: list[CardInfo] = []
    for c in detected:
        matched: Optional[str] = None
        if c.label:
            r = await db.execute(
                select(SyncProfile).where(
                    SyncProfile.enabled == True,
                    SyncProfile.match_type == "label",
                    SyncProfile.match_value == c.label,
                )
            )
            p = r.scalar_one_or_none()
            if p:
                matched = p.name
        result.append(CardInfo(
            path=c.path,
            label=c.label,
            total_space=c.total_space,
            used_space=c.used_space,
            matched_profile=matched,
        ))
    return result


@router.get("/{path:path}/preview", response_model=list[FilePreview])
async def preview_card(path: str, file_types: str = Query("photos")):
    if not os.path.isdir(path):
        raise as_http_exception(CardNotFoundError())
    filters = {"photos": True, "videos": file_types == "all"}
    return [
        FilePreview(
            name=f["name"],
            path=f["path"],
            size=f["size"],
            modified=str(f["mtime"]),
        )
        for f in scan_files(path, filters)
    ]
