"""
PhotoSync — async thumbnail generation via shared executor.
"""

from __future__ import annotations

import hashlib
import asyncio
import os
from io import BytesIO
from typing import Optional

from PIL import Image

from app.executors import get_thumb_executor
from app.constants import DEFAULT_THUMBNAIL_DIR, DEFAULT_THUMBNAIL_SIZE


def _get_jpeg_preview(raw_path: str) -> Optional[bytes]:
    """Extract embedded JPEG preview from a raw photo file."""
    try:
        with open(raw_path, "rb") as f:
            data = f.read()
        idx = data.find(b"\xff\xd8\xff")
        if idx >= 0:
            eoi = data.find(b"\xff\xd9", idx)
            if eoi >= 0:
                return data[idx : eoi + 2]
    except Exception:
        pass
    return None


def _generate_thumb(image_path: str, thumb_path: str, size: int = DEFAULT_THUMBNAIL_SIZE) -> bool:
    """Synchronous thumbnail generation (runs in executor)."""
    try:
        ext = os.path.splitext(image_path)[1].lower()
        raw_exts = {".arw", ".cr2", ".cr3", ".nef", ".raf", ".dng", ".orf", ".rw2"}

        if ext in raw_exts:
            preview = _get_jpeg_preview(image_path)
            if preview:
                img = Image.open(BytesIO(preview))
            else:
                return False
        else:
            img = Image.open(image_path)

        img.thumbnail((size, size), Image.LANCZOS)
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(thumb_path, "JPEG", quality=85)
        return True
    except Exception:
        return False


async def generate_thumbnail(
    image_path: str,
    thumbnail_dir: str = DEFAULT_THUMBNAIL_DIR,
    size: int = DEFAULT_THUMBNAIL_SIZE,
) -> Optional[str]:
    """Generate a thumbnail for *image_path*, returning the thumbnail path
    (or ``None`` on failure)."""
    fh = hashlib.sha256(image_path.encode()).hexdigest()[:16]
    tp = os.path.join(thumbnail_dir, f"{fh}.jpg")
    if os.path.exists(tp):
        return tp

    loop = asyncio.get_running_loop()
    ok = await loop.run_in_executor(get_thumb_executor(), _generate_thumb, image_path, tp, size)
    return tp if ok else None
