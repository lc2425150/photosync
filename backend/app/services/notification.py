"""
PhotoSync — multi-channel notification dispatcher.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NotificationConfig

logger = logging.getLogger("photosync.notification")


class NotificationService:
    """Send notifications (Telegram / DingTalk / WeChat / Email / Webhook)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def send_all(self, title: str, message: str, level: str = "info") -> None:
        r = await self.db.execute(
            select(NotificationConfig).where(NotificationConfig.enabled == True)
        )
        for cfg in r.scalars().all():
            try:
                await self._send(cfg.type, cfg.config, title, message, level)
            except Exception as e:
                logger.error("[通知] %s 发送失败: %s", cfg.type, e)

    async def _send(self, t: str, c: dict, title: str, msg: str, level: str) -> None:
        if t == "telegram":
            await self._tg(c, title, msg)
        elif t == "dingtalk":
            await self._ding(c, title, msg)
        elif t == "wechat":
            await self._wx(c, title, msg)
        elif t == "email":
            await self._mail(c, title, msg)
        elif t == "webhook":
            await self._hook(c, title, msg, level)

    async def _tg(self, c: dict, title: str, msg: str) -> None:
        bt = c.get("bot_token")
        ci = c.get("chat_id")
        if not bt or not ci:
            return
        async with httpx.AsyncClient() as cl:
            await cl.post(
                f"https://api.telegram.org/bot{bt}/sendMessage",
                json={
                    "chat_id": ci,
                    "text": f"*{title}*\n{msg}",
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )

    async def _ding(self, c: dict, title: str, msg: str) -> None:
        url = c.get("webhook_url")
        if not url:
            return
        async with httpx.AsyncClient() as cl:
            await cl.post(
                url,
                json={
                    "msgtype": "markdown",
                    "markdown": {"title": title, "text": f"## {title}\n{msg}"},
                },
                timeout=10,
            )

    async def _wx(self, c: dict, title: str, msg: str) -> None:
        url = c.get("webhook_url")
        if not url:
            return
        async with httpx.AsyncClient() as cl:
            await cl.post(
                url,
                json={
                    "msgtype": "markdown",
                    "markdown": {"content": f"## {title}\n{msg}"},
                },
                timeout=10,
            )

    async def _mail(self, c: dict, title: str, msg: str) -> None:
        host = c.get("smtp_host")
        port = c.get("smtp_port", 587)
        user = c.get("username")
        pw = c.get("password")
        to = c.get("to_address")
        if not all([host, user, pw, to]):
            return
        m = MIMEText(msg, "plain", "utf-8")
        m["Subject"] = title
        m["From"] = user
        m["To"] = to
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(m)

    async def _hook(self, c: dict, title: str, msg: str, level: str) -> None:
        url = c.get("url")
        if not url:
            return
        async with httpx.AsyncClient() as cl:
            await cl.post(
                url,
                json={"title": title, "message": msg, "level": level},
                timeout=10,
            )
