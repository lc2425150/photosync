"""
PhotoSync — sync profile CRUD + import/export router.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncProfile
from app.schemas import ProfileCreate, ProfileUpdate, ProfileResponse, PaginatedResponse
from app.exceptions import ProfileNotFoundError, as_http_exception
from app.config import settings

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


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
    items = [ProfileResponse.model_validate(p) for p in r.scalars().all()]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{pid:int}", response_model=ProfileResponse)
async def get_profile(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    return ProfileResponse.model_validate(p)


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    p = SyncProfile(**data.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return ProfileResponse.model_validate(p)


@router.put("/{pid:int}", response_model=ProfileResponse)
async def update_profile(pid: int, data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p:
        raise as_http_exception(ProfileNotFoundError())
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return ProfileResponse.model_validate(p)


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
    return ProfileResponse.model_validate(p)


@router.post("/import", response_model=ProfileResponse, status_code=201)
async def import_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    p = SyncProfile(**data.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return ProfileResponse.model_validate(p)
