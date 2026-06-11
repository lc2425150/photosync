"""
PhotoSync — sync profile CRUD + import/export router.
The ``destination`` field is auto-translated between host ↔ container paths.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncProfile
from app.schemas import ProfileCreate, ProfileUpdate, ProfileResponse, PaginatedResponse
from app.exceptions import ProfileNotFoundError, as_http_exception
from app.path_mapper import to_host, to_container

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


def _profile_to_response(p: SyncProfile) -> ProfileResponse:
    """Convert ORM model to response, translating destination to host path."""
    data = ProfileResponse.model_validate(p).model_dump()
    data["destination"] = to_host(data["destination"])
    return ProfileResponse(**data)


@router.get("", response_model=PaginatedResponse)
async def list_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(SyncProfile).order_by(SyncProfile.created_at.desc())
    if enabled is not None:
        q = q.where(SyncProfile.enabled == enabled)
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    r = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = [_profile_to_response(p) for p in r.scalars().all()]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{pid:int}", response_model=ProfileResponse)
async def get_profile(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    return _profile_to_response(p)


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    payload = data.model_dump()
    payload["destination"] = to_container(payload["destination"])
    p = SyncProfile(**payload)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _profile_to_response(p)


@router.put("/{pid:int}", response_model=ProfileResponse)
async def update_profile(pid: int, data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    updates = data.model_dump(exclude_unset=True)
    if "destination" in updates:
        updates["destination"] = to_container(updates["destination"])
    for k, v in updates.items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return _profile_to_response(p)


@router.delete("/{pid:int}")
async def delete_profile(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    await db.delete(p)
    await db.commit()
    return {"ok": True}


@router.get("/{pid:int}/export", response_model=ProfileResponse)
async def export_profile(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    return _profile_to_response(p)


@router.post("/import", response_model=ProfileResponse, status_code=201)
async def import_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    payload = data.model_dump()
    payload["destination"] = to_container(payload["destination"])
    p = SyncProfile(**payload)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _profile_to_response(p)
