"""
Integration tests for PhotoSync API.
Overrides the DB URL to use a temp file before importing the app.
"""
import os, sys, tempfile

# 1. Override settings BEFORE any app imports
_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="ps_test_")
os.close(_db_fd)

import app.config
app.config.settings.database_url = f"sqlite+aiosqlite:///{_db_path}"

# 2. Now safe to import app (engine uses the overridden URL)
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db, engine


@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await engine.dispose()
    try:
        os.remove(_db_path)
    except FileNotFoundError:
        pass


@pytest.mark.asyncio
class TestAPI:
    async def test_health(self, client):
        r = await client.get("/api/v1/system/health")
        assert r.status_code == 200
        assert r.json()["status"] in ("healthy", "degraded")

    async def test_profiles_crud(self, client):
        r = await client.post("/api/v1/profiles", json={
            "name": "Test Profile", "match_type": "manual", "destination": "/photos/test",
        })
        assert r.status_code == 201
        pid = r.json()["id"]
        r = await client.get(f"/api/v1/profiles/{pid}")
        assert r.status_code == 200
        r = await client.put(f"/api/v1/profiles/{pid}", json={"name": "Updated"})
        assert r.status_code == 200 and r.json()["name"] == "Updated"
        r = await client.delete(f"/api/v1/profiles/{pid}")
        assert r.status_code == 200

    async def test_settings(self, client):
        r = await client.put("/api/v1/settings", json={"poll_interval": 10})
        assert r.status_code == 200
        r = await client.get("/api/v1/settings")
        assert r.status_code == 200
        assert r.json()["poll_interval"] == 10
