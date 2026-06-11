"""
PhotoSync — dynamic settings router (persisted in DB).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Setting
from app.schemas import SettingsUpdate
from app.config import settings as app_settings

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

# Single source of truth — these match app.config.Settings defaults.
_DEFAULTS: dict[str, object] = {
    "scan_paths": app_settings.scan_paths,
    "poll_interval": app_settings.poll_interval,
    "default_destination": app_settings.default_destination,
    "max_concurrent_copies": app_settings.max_concurrent_copies,
    "log_retention_days": app_settings.log_retention_days,
    "history_retention_days": app_settings.history_retention_days,
}


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Setting))
    merged = dict(_DEFAULTS)
    for row in r.scalars().all():
        merged[row.key] = row.value
    return merged


@router.put("")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    for k, v in data.model_dump(exclude_unset=True).items():
        existing = await db.get(Setting, k)
        if existing:
            existing.value = v
        else:
            db.add(Setting(key=k, value=v))
    await db.commit()

    r = await db.execute(select(Setting))
    merged = dict(_DEFAULTS)
    for row in r.scalars().all():
        merged[row.key] = row.value
    return merged
