"""
PhotoSync — Pydantic request/response schemas.

Every API endpoint should return a schema, not a raw dict.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

# ── Helpers ─────────────────────────────────────────────────────────

def _opt(**kwargs: Any) -> Any:
    """Shortcut for Optional fields with default None."""
    return Field(default=None, **kwargs)


# ── Profiles ────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    match_type: str = "manual"
    match_value: Optional[str] = None
    destination: str = "/photos"
    sync_mode: str = "date"
    custom_template: Optional[str] = None
    file_filters: Optional[dict[str, Any]] = None
    conflict_strategy: str = "skip"
    copy_mode: str = "copy"
    auto_eject: bool = False
    checksum_verify: bool = True
    auto_sync: bool = False
    poll_interval: int = 5
    enabled: bool = True


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    match_type: Optional[str] = None
    match_value: Optional[str] = None
    destination: Optional[str] = None
    sync_mode: Optional[str] = None
    custom_template: Optional[str] = None
    file_filters: Optional[dict[str, Any]] = None
    conflict_strategy: Optional[str] = None
    copy_mode: Optional[str] = None
    auto_eject: Optional[bool] = None
    checksum_verify: Optional[bool] = None
    auto_sync: Optional[bool] = None
    poll_interval: Optional[int] = None
    enabled: Optional[bool] = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    match_type: str
    match_value: Optional[str] = None
    destination: str
    sync_mode: str
    custom_template: Optional[str] = None
    file_filters: Optional[dict[str, Any]] = None
    conflict_strategy: str
    copy_mode: str
    auto_eject: bool
    checksum_verify: bool
    auto_sync: bool
    poll_interval: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── History ─────────────────────────────────────────────────────────

class SyncFileResponse(BaseModel):
    id: int
    filename: str
    relative_path: Optional[str] = None
    file_size: int
    checksum: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    id: int
    profile_id: Optional[int] = None
    profile_name: Optional[str] = None
    status: str
    total_files: int = 0
    synced_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    total_bytes: int = 0
    synced_bytes: int = 0
    source_path: Optional[str] = None
    dest_path: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class HistoryDetailResponse(HistoryResponse):
    files: list[SyncFileResponse] = []


# ── Cards ───────────────────────────────────────────────────────────

class CardInfo(BaseModel):
    path: str
    label: str
    total_space: Optional[int] = None
    used_space: Optional[int] = None
    matched_profile: Optional[str] = None


class FilePreview(BaseModel):
    name: str
    path: str
    size: int
    is_dir: bool = False
    modified: Optional[str] = None


# ── Gallery ─────────────────────────────────────────────────────────

class GalleryPhoto(BaseModel):
    id: int
    filename: str
    file_size: int
    dest_path: Optional[str] = None
    created_at: str
    thumbnail_url: str
    image_url: str


class GalleryResponse(BaseModel):
    items: list[GalleryPhoto]
    total: int
    page: int
    page_size: int


# ── Sync ────────────────────────────────────────────────────────────

class SyncStatusResponse(BaseModel):
    running: bool = False
    current_file: Optional[str] = None
    current: int = 0
    total: int = 0
    current_bytes: int = 0
    total_bytes: int = 0
    speed_mbps: Optional[float] = None
    eta_seconds: Optional[int] = None
    elapsed_seconds: int = 0
    queue_length: int = 0


class DryRunResponse(BaseModel):
    total_files: int = 0
    total_size: int = 0
    new_files: int = 0
    new_size: int = 0
    skipped_files: int = 0
    skipped_size: int = 0
    files: list[dict[str, Any]] = []


class QueueItemResponse(BaseModel):
    id: int
    card_path: str
    card_label: Optional[str] = None
    profile_id: Optional[int] = None
    status: str
    queued_at: datetime

    model_config = {"from_attributes": True}


# ── Settings ────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    scan_paths: Optional[list[str]] = None
    poll_interval: Optional[int] = None
    default_destination: Optional[str] = None
    max_concurrent_copies: Optional[int] = None
    log_retention_days: Optional[int] = None
    history_retention_days: Optional[int] = None


# ── Notifications ───────────────────────────────────────────────────

class NotificationConfigCreate(BaseModel):
    type: str = Field(..., pattern=r"^(telegram|dingtalk|wechat|email|webhook)$")
    enabled: bool = True
    config: dict[str, Any]


class NotificationConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict[str, Any]] = None


class NotificationConfigResponse(BaseModel):
    id: int
    type: str
    enabled: bool
    config: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── System ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    worker: dict[str, Any]
    db: dict[str, Any]
    version: str


class StorageItem(BaseModel):
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float


class LogEntry(BaseModel):
    id: int
    level: str
    message: str
    timestamp: str


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


# ── Generic ─────────────────────────────────────────────────────────

class OkResponse(BaseModel):
    ok: bool = True


class ErrorDetail(BaseModel):
    code: str = "UNKNOWN"
    message: str = "未知错误"


class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(default_factory=lambda: ErrorDetail())
