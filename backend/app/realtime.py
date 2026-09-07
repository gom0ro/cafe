from typing import Set
from fastapi import WebSocket


_connections: Set[WebSocket] = set()


async def register(websocket: WebSocket):
    _connections.add(websocket)


async def unregister(websocket: WebSocket):
    _connections.discard(websocket)


async def broadcast(payload: str):
    if not _connections:
        return
    stale = []
    for ws in list(_connections):
        try:
            await ws.send_text(payload)
        except Exception:
            stale.append(ws)
    for ws in stale:
        _connections.discard(ws)