"""
PhotoSync — FastAPI application entry point.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import init_db, engine
from app.middleware import register_middleware
from app.services.ws_manager import ws_manager
from app.executors import shutdown_executors
from app.worker import start_worker, stop_worker

# ── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("photosync")

# ── Lifespan ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PhotoSync 启动中 ...")
    await init_db()
    worker_task = asyncio.create_task(start_worker())
    yield
    logger.info("PhotoSync 关闭中 ...")
    await stop_worker()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await shutdown_executors()
    await engine.dispose()

# ── Application ─────────────────────────────────────────────────────

app = FastAPI(
    title="PhotoSync",
    description="NAS 相机储存卡自动同步系统",
    version=settings.app_version,
    lifespan=lifespan,
)

register_middleware(app)

# ── Static files ────────────────────────────────────────────────────

STATIC_DIR = Path("/app/static")
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Health endpoint ─────────────────────────────────────────────────

@app.get("/api/v1/system/health", tags=["system"])
async def health():
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    return {
        "status": "healthy" if db_ok else "degraded",
        "worker": {"alive": True},
        "db": {"connected": db_ok},
        "version": settings.app_version,
    }


# ── WebSocket ───────────────────────────────────────────────────────

@app.websocket("/api/v1/ws/sync/status")
async def ws_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except (WebSocketDisconnect, Exception):
        ws_manager.disconnect(ws)


# ── Routers ─────────────────────────────────────────────────────────

from app.routers import profiles as _profiles, sync as _sync, cards as _cards, history as _history, gallery as _gallery, settings as _settings_router, notifications as _notifications, system as _system

app.include_router(_profiles.router)
app.include_router(_sync.router)
app.include_router(_cards.router)
app.include_router(_history.router)
app.include_router(_gallery.router)
app.include_router(_settings_router.router)
app.include_router(_notifications.router)
app.include_router(_system.router)


# ── SPA catch-all (must be last) ────────────────────────────────────

@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": "not found"})
    index = STATIC_DIR / "index.html"
    if index.is_file():
        return HTMLResponse(content=index.read_text(encoding="utf-8"))
    return RedirectResponse(url="/static/index.html")
