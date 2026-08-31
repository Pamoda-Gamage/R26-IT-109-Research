from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Chat
from app.connection_manager import manager

router = APIRouter()


@router.websocket("/ws/chats/{chat_id}")
async def chat_socket(websocket: WebSocket, chat_id: str):
    # Own DB session — get_db() as a FastAPI Depends doesn't work cleanly
    # inside a websocket route the way it does for HTTP, so open/close manually.
    db: Session = SessionLocal()
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            await websocket.close(code=4404)  # custom code: chat not found
            return

        await manager.connect(chat_id, websocket)

        # On connect, replay history so a freshly opened tab/device is caught up
        # without a separate REST round trip.
        await websocket.send_json({
            "type": "history",
            "messages": [m.serialize() for m in chat.messages],
        })

        # If a background pipeline is mid-flight for this chat, tell the freshly
        # connected tab what stage it's at so a progress stepper can resume.
        current_stage = manager.get_stage(chat_id)
        if current_stage:
            await websocket.send_json(current_stage)

        try:
            while True:
                # We don't require the client to send anything, but keep the
                # loop alive to detect disconnects and to support optional
                # client->server events (typing indicators, pings, read receipts).
                msg = await websocket.receive_json()
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                # Extend here for e.g. {"type": "typing"} broadcasts to other
                # connections in the same room if you want multi-device presence.
        except WebSocketDisconnect:
            manager.disconnect(chat_id, websocket)
    finally:
        db.close()