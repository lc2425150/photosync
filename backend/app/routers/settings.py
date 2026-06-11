"""
PhotoSync — dynamic settings router (persisted in DB).
Stores container paths internally, but accepts/returns host paths
via automatic translation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Setting
from app.schemas import SettingsUpdate
from app.config import settings as app_settings
from app.path_mapper import to_host, to_container

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

# Keys that contain filesystem paths
_PATH_KEYS = frozenset({"default_destination", "scan_paths"})

_DEFAULTS: dict[str, object] = {
    "scan_paths": app_settings.scan_paths,
    "poll_interval": app_settings.poll_interval,
    "default_destination": app_settings.default_destination,
    "max_concurrent_copies": app_settings.max_concurrent_copies,
    "log_retention_days": app_settings.log_retention_days,
    "history_retention_days": app_settings.history_retention_days,
}


def _translate_value(key: str, value: object, to_host_side: bool) -> object:
    """Translate a single setting value between host↔container paths."""
    if key == "default_destination" and isinstance(value, str):
        return to_host(value) if to_host_side else to_container(value)
    if key == "scan_paths" and isinstance(value, list):
        if to_host_side:
            # scan_paths are always container paths, no translation needed
            return value
    return value


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Setting))
    merged = dict(_DEFAULTS)
    for row in r.scalars().all():
        merged[row.key] = row.value
    # Translate stored container paths → host paths for display
    merged["default_destination"] = _translate_value(
        "default_destination", merged.get("default_destination", "/photos"), True
    )
    return merged


@router.put("")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    for k, v in data.model_dump(exclude_unset=True).items():
        # Translate host path → container path for storage
        if k in _PATH_KEYS:
            v = _translate_value(k, v, False)
        existing = await db.get(Setting, k)
        if existing:
            existing.value = v
        else:
            db.add(Setting(key=k, value=v))
    await db.commit()

    # Return all settings with host paths
    r = await db.execute(select(Setting))
    merged = dict(_DEFAULTS)
    for row in r.scalars().all():
        merged[row.key] = row.value
    merged["default_destination"] = _translate_value(
        "default_destination", merged.get("default_destination", "/photos"), True
    )
    return merged
