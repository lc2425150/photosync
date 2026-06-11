"""
PhotoSync — domain exception classes with structured error codes.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class PhotoSyncError(Exception):
    """Base exception for all domain errors."""

    def __init__(
        self, code: str = "UNKNOWN", message: str = "未知错误", status_code: int = 500
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message}}


class NotFoundError(PhotoSyncError):
    def __init__(
        self, code: str = "NOT_FOUND", message: str = "资源不存在"
    ) -> None:
        super().__init__(code=code, message=message, status_code=404)


class ProfileNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__(code="PROFILE_NOT_FOUND", message="同步配置不存在")


class CardNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__(code="CARD_NOT_FOUND", message="储存卡路径不存在")


class FileNotFoundError_(NotFoundError):
    def __init__(self) -> None:
        super().__init__(code="FILE_NOT_FOUND", message="文件不存在")


class NotificationNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_NOT_FOUND", message="通知配置不存在")


class QueueNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__(code="QUEUE_NOT_FOUND", message="队列项不存在")


class NotificationSendError(PhotoSyncError):
    def __init__(self, detail: str = "") -> None:
        msg = f"通知发送失败: {detail}" if detail else "通知发送失败"
        super().__init__(code="NOTIFICATION_SEND_FAILED", message=msg, status_code=502)


class ValidationError(PhotoSyncError):
    def __init__(self, message: str = "参数验证失败", code: str = "VALIDATION_ERROR") -> None:
        super().__init__(code=code, message=message, status_code=422)


class SyncInProgressError(PhotoSyncError):
    def __init__(self) -> None:
        super().__init__(
            code="SYNC_IN_PROGRESS",
            message="同步进行中，请先取消当前同步",
            status_code=409,
        )


def as_http_exception(err: PhotoSyncError) -> HTTPException:
    """Convert a domain exception to a FastAPI HTTPException."""
    return HTTPException(status_code=err.status_code, detail=err.to_dict())
