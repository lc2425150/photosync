"""
PhotoSync — notification config CRUD + test router.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import NotificationConfig
from app.schemas import (
    NotificationConfigCreate,
    NotificationConfigUpdate,
    NotificationConfigResponse,
    OkResponse,
)
from app.exceptions import (
    NotificationNotFoundError,
    NotificationSendError,
    as_http_exception,
)
from app.services.notification import NotificationService

logger = logging.getLogger("photosync.notifications")

router = APIRouter(prefix="/api/v1/notification-configs", tags=["notifications"])


@router.get("", response_model=list[NotificationConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(NotificationConfig))
    return [NotificationConfigResponse.model_validate(c) for c in r.scalars().all()]


@router.post("", response_model=NotificationConfigResponse, status_code=201)
async def create_config(data: NotificationConfigCreate, db: AsyncSession = Depends(get_db)):
    c = NotificationConfig(type=data.type, enabled=data.enabled, config=data.config)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return NotificationConfigResponse.model_validate(c)


@router.put("/{cid:int}", response_model=NotificationConfigResponse)
async def update_config(cid: int, data: NotificationConfigUpdate, db: AsyncSession = Depends(get_db)):
    c = await db.get(NotificationConfig, cid)
    if not c:
        raise as_http_exception(NotificationNotFoundError())
    if data.enabled is not None:
        c.enabled = data.enabled
    if data.config is not None:
        c.config = data.config
    await db.commit()
    await db.refresh(c)
    return NotificationConfigResponse.model_validate(c)


@router.delete("/{cid:int}", response_model=OkResponse)
async def delete_config(cid: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(NotificationConfig, cid)
    if not c:
        raise as_http_exception(NotificationNotFoundError())
    await db.delete(c)
    await db.commit()
    return OkResponse()


@router.post("/test", response_model=OkResponse)
async def test_notification(cid: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(NotificationConfig, cid)
    if not c:
        raise as_http_exception(NotificationNotFoundError())
    try:
        svc = NotificationService(db)
        await svc._send(c.type, c.config, "PhotoSync 测试", "这是一条测试消息", "info")
        return OkResponse()
    except Exception as e:
        logger.error("测试通知发送失败 (cid=%s): %s", cid, e)
        raise as_http_exception(NotificationSendError(detail=str(e)))
