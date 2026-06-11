"""
PhotoSync — filesystem scanner that walks directories
and yields matched files.
"""

from __future__ import annotations

import os
from typing import Generator, Optional

from app.constants import (
    PHOTO_EXTENSIONS,
    VIDEO_EXTENSIONS,
    RAW_EXTENSIONS,
    SIDECAR_EXTENSIONS,
    IGNORED_FILES,
)


def sanitize_filename(name: str, max_length: int = 255) -> str:
    """Remove illegal filesystem characters and truncate."""
    illegal = r'\/:*?"<>|'
    for c in illegal:
        name = name.replace(c, "_")
    name = name.strip(". ")
    if len(name) > max_length:
        base, ext = os.path.splitext(name)
        name = base[: max_length - len(ext)] + ext
    return name if name else "_"


def matches_filters(filename: str, filters: Optional[dict] = None) -> bool:
    """Check whether *filename* passes the given *filters* dict."""
    name_lower = filename.lower()
    ext = os.path.splitext(name_lower)[1]

    # Always skip macOS metadata / system files
    if name_lower.startswith("._") or name_lower in IGNORED_FILES:
        return False

    if not filters:
        return ext in PHOTO_EXTENSIONS or ext in VIDEO_EXTENSIONS

    allowed: set[str] = set()
    if filters.get("photos", True):
        allowed.update(PHOTO_EXTENSIONS)
    if filters.get("videos", False):
        allowed.update(VIDEO_EXTENSIONS)
    if filters.get("raw_only", False):
        allowed = set(RAW_EXTENSIONS)
    if filters.get("sidecar", False):
        allowed.update(SIDECAR_EXTENSIONS)
    if filters.get("custom_extensions"):
        allowed.update(
            e if e.startswith(".") else f".{e}"
            for e in filters["custom_extensions"]
        )
    return ext in allowed


def scan_files(
    path: str, filters: Optional[dict] = None
) -> Generator[dict, None, None]:
    """
    Walk *path* recursively and yield dicts for every file that passes
    *filters*.

    Yields
        dict with keys: path, name, relative_path, size, mtime
    """
    for root, dirs, files in os.walk(path):
        dirs[:] = [
            d
            for d in dirs
            if d.lower() not in IGNORED_FILES and not d.startswith(".")
        ]
        for file in files:
            if not matches_filters(file, filters):
                continue
            fp = os.path.join(root, file)
            try:
                s = os.stat(fp)
                yield {
                    "path": fp,
                    "name": file,
                    "relative_path": os.path.relpath(fp, path),
                    "size": s.st_size,
                    "mtime": s.st_mtime,
                }
            except OSError:
                continue


def detect_sidecar_files(photo_path: str) -> list[str]:
    """Return paths of sidecar files that exist next to *photo_path*."""
    base = os.path.splitext(photo_path)[0]
    return [base + ext for ext in SIDECAR_EXTENSIONS if os.path.exists(base + ext)]
