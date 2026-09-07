from fastapi import WebSocket
from app import realtime


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await realtime.register(websocket)
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
    except Exception:
        pass
    finally:
        await realtime.unregister(websocket)
        try:
            await websocket.close()
        except Exception:
            pass