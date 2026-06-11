"""
PhotoSync — FastAPI middleware: CORS, request logging, global error handler.
"""

import time
import logging
from typing import Callable, Awaitable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

from app.exceptions import PhotoSyncError

logger = logging.getLogger("photosync.http")


def register_middleware(app: FastAPI) -> None:
    """Register all middleware and exception handlers on the FastAPI app."""

    # ── CORS (allow all origins for development / NAS local network) ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing / logging middleware ──
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable[[Request], Awaitable]):
        start = time.monotonic()
        response = await call_next(request)
        elapsed = time.monotonic() - start
        if elapsed > 0.5:
            logger.warning(
                "slow request | %s %s | %s | %.2fs",
                request.method, request.url.path, response.status_code, elapsed,
            )
        return response

    # ── Global domain-exception handler ──
    @app.exception_handler(PhotoSyncError)
    async def photosync_error_handler(request: Request, exc: PhotoSyncError):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    # ── Catch-all 500 handler ──
    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "服务内部错误"}},
        )
