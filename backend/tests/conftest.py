"""Shared fixtures for PhotoSync tests.

Overrides the DB URL *before* any engine is created, then imports
``app.database.Base`` so all model tables register correctly.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./.test_photosync.db")
import app.config

app.config.settings.database_url = "sqlite+aiosqlite:///./.test_photosync.db"

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, class_=AsyncSession)()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()


@pytest.fixture
def mock_card_dir(tmp_path):
    """Create a fake card directory for file-scanning tests.
    This directory is NOT treated as a detected card (no mount).
    """
    card = tmp_path / "SDCARD"
    card.mkdir()
    dcim = card / "DCIM"
    dcim.mkdir()
    (dcim / "DSC_0001.ARW").write_bytes(b"mock_raw_001")
    (dcim / "DSC_0002.JPG").write_bytes(b"mock_jpg_002")
    (dcim / "DSC_0003.MP4").write_bytes(b"mock_vid_003")
    (dcim / "._DSC_0001.ARW").write_bytes(b"macos_meta")
    return str(card)
