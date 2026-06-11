"""
PhotoSync — SHA-256 checksum utilities (async via shared executor).
"""

from __future__ import annotations

import hashlib
import asyncio

from app.executors import get_io_executor


async def calculate_sha256(filepath: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_io_executor(), _sha256, filepath)


def _sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


async def verify_checksum(filepath: str, expected_hash: str) -> bool:
    return (await calculate_sha256(filepath)) == expected_hash
