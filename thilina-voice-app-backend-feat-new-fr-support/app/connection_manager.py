"""
Tracks live WebSocket connections per chat_id ("room"). A user can have
several tabs/devices open on the same chat (e.g. dispatcher + field tech),
so this is chat_id -> set[WebSocket], not a single connection.

This is process-local. Fine for a single backend instance. If you scale to
multiple instances behind a load balancer, replace this with a Redis
pub/sub channel per chat_id so a broadcast from instance A reaches a
websocket connected to instance B.
"""
from fastapi import WebSocket
from collections import defaultdict


class ConnectionManager:
    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # Last "stage" event per chat while a background pipeline is running,
        # so a tab that connects (or reconnects) mid-processing can be told
        # what the backend is currently doing. Cleared when the pipeline ends.
        self._stage: dict[str, dict] = {}

    async def connect(self, chat_id: str, websocket: WebSocket):
        await websocket.accept()
        self._rooms[chat_id].add(websocket)

    def set_stage(self, chat_id: str, payload: dict):
        self._stage[chat_id] = payload

    def get_stage(self, chat_id: str) -> dict | None:
        return self._stage.get(chat_id)

    def clear_stage(self, chat_id: str):
        self._stage.pop(chat_id, None)

    def disconnect(self, chat_id: str, websocket: WebSocket):
        self._rooms[chat_id].discard(websocket)
        if not self._rooms[chat_id]:
            del self._rooms[chat_id]

    async def broadcast(self, chat_id: str, payload: dict):
        """Send to every connection currently open on this chat. Silently
        drops connections that have gone stale rather than raising, since
        a background task calling this shouldn't crash on a closed socket."""
        dead = []
        for ws in self._rooms.get(chat_id, set()):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._rooms[chat_id].discard(ws)


manager = ConnectionManager()