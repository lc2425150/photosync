"""
PhotoSync — application configuration via environment / .env file.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

import app.constants as c


class Settings(BaseSettings):
    """Config loaded from environment variables or `.env` file."""

    # ── Meta ──
    app_name: str = "PhotoSync"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── Database ──
    database_url: str = "sqlite+aiosqlite:////app/data/photosync.db"

    # ── Card detection ──
    scan_paths: list[str] = c.DEFAULT_SCAN_PATHS
    poll_interval: int = c.DEFAULT_POLL_INTERVAL

    # ── Sync ──
    default_destination: str = c.DEFAULT_DESTINATION
    max_concurrent_copies: int = c.DEFAULT_MAX_CONCURRENT_COPIES
    max_queue_size: int = c.DEFAULT_MAX_QUEUE_SIZE

    # ── Thumbnails ──
    thumbnail_dir: str = c.DEFAULT_THUMBNAIL_DIR
    thumbnail_size: int = c.DEFAULT_THUMBNAIL_SIZE

    # ── Cleanup ──
    log_retention_days: int = c.DEFAULT_LOG_RETENTION_DAYS
    history_retention_days: int = c.DEFAULT_HISTORY_RETENTION_DAYS

    # ── Path mapping ──
    photos_mount_host_path: str = "/volume2/Photos"

    # ── Misc ──
    tz: str = "Asia/Shanghai"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
