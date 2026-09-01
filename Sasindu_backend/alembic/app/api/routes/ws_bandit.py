import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
_subscribers: set[WebSocket] = set()


async def broadcast_bandit_state(state: dict) -> None:
    dead = []
    for ws in _subscribers:
        try:
            await ws.send_json(state)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _subscribers.discard(ws)


@router.websocket("/ws/bandit")
async def bandit_stream(websocket: WebSocket):
    await websocket.accept()
    _subscribers.add(websocket)
    try:
        while True:
            await asyncio.sleep(3600)
    except WebSocketDisconnect:
        _subscribers.discard(websocket)
