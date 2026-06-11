"""
PhotoSync — WebSocket connection manager for real-time progress updates.
"""

from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    """Track active WebSocket connections and broadcast JSON messages."""

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: dict) -> None:
        dead: set[WebSocket] = set()
        for c in self.active:
            try:
                await c.send_json(message)
            except Exception:
                dead.add(c)
        self.active -= dead


ws_manager = ConnectionManager()
