"""
PhotoSync — shared constants and enumerations.
"""

from __future__ import annotations

import enum
from typing import Final

# ── File type extensions ────────────────────────────────────────────

PHOTO_EXTENSIONS: Final[frozenset[str]] = frozenset({
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
    '.arw', '.cr2', '.cr3', '.nef', '.nrw', '.raf', '.dng', '.orf',
    '.rw2', '.pef', '.srw', '.x3f', '.3fr',
})

VIDEO_EXTENSIONS: Final[frozenset[str]] = frozenset({
    '.mp4', '.mov', '.avi', '.mkv', '.mts', '.m2ts', '.mpg', '.mpeg',
})

RAW_EXTENSIONS: Final[frozenset[str]] = frozenset({
    '.arw', '.cr2', '.cr3', '.nef', '.nrw', '.raf', '.dng', '.orf',
    '.rw2', '.pef', '.srw', '.x3f', '.3fr',
})

SIDECAR_EXTENSIONS: Final[frozenset[str]] = frozenset({'.xmp', '.pp3', '.dop', '.sidecar'})

# ── Ignored file / directory names ─────────────────────────────────

IGNORED_FILES: Final[frozenset[str]] = frozenset({
    '.ds_store', 'thumbs.db', 'desktop.ini', '.trashes',
    '.fseventsd', '.spotlight-v100',
})

# Directories commonly created by NAS / OS that should NOT be treated
# as removable storage cards even if they appear under scan paths.
IGNORED_MOUNT_DIRS: Final[frozenset[str]] = frozenset({
    # Synology / generic NAS
    '@eadir', '@share', '@database', '@synology',
    '#recycle', '.recycle', '.recycles',
    # macOS / Finder
    '.stationary', '.localized',
    # Linux
    'lost+found',
})

# ── Thumbnail defaults ─────────────────────────────────────────────

DEFAULT_THUMBNAIL_DIR: str = "/app/data/thumbnails"
DEFAULT_THUMBNAIL_SIZE: int = 300

# ── DB / cleanup defaults ──────────────────────────────────────────

DEFAULT_LOG_RETENTION_DAYS: int = 90
DEFAULT_HISTORY_RETENTION_DAYS: int = 365

# ── Sync ───────────────────────────────────────────────────────────

DEFAULT_POLL_INTERVAL: int = 5
DEFAULT_MAX_CONCURRENT_COPIES: int = 4
DEFAULT_SCAN_PATHS: list[str] = ["/media", "/mnt", "/run/media"]
DEFAULT_DESTINATION: str = "/photos"
DEFAULT_MAX_QUEUE_SIZE: int = 10000


# ── Application level enums ────────────────────────────────────────

class SyncMode(str, enum.Enum):
    DATE = "date"
    ORIGINAL = "original"
    CUSTOM = "custom"


class MatchType(str, enum.Enum):
    LABEL = "label"
    ALWAYS = "always"
    MANUAL = "manual"


class ConflictStrategy(str, enum.Enum):
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    KEEP_BOTH = "keep_both"


class CopyMode(str, enum.Enum):
    COPY = "copy"
    MOVE = "move"


class SyncStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileSyncStatus(str, enum.Enum):
    SYNCED = "synced"
    SKIPPED = "skipped"
    FAILED = "failed"


class QueueStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
