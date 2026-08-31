import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class ChatStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class MessageSender(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class MessageType(str, enum.Enum):
    text = "text"
    audio = "audio"
    image = "image"


class MessageStatus(str, enum.Enum):
    processing = "processing"
    complete = "complete"
    failed = "failed"


class Chat(Base):
    """
    A single dispatch case / conversation thread. Everything routes through
    a chat_id — that's the "room" both HTTP responses and WebSocket
    broadcasts key off of, so multiple simultaneous cases for the same user
    never cross wires.
    """
    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, index=True, nullable=False)  # see auth note in routers/chats.py
    title = Column(String, default="New request")
    status = Column(Enum(ChatStatus), default=ChatStatus.open)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    messages = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=new_id)
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False, index=True)

    sender = Column(Enum(MessageSender), nullable=False)
    type = Column(Enum(MessageType), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.complete)

    content = Column(Text, nullable=True)       # transcript / typed text / assistant reply
    translation = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)   # for image/audio playback
    classification = Column(Text, nullable=True)  # JSON-encoded intent/service/urgency
    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=now)

    chat = relationship("Chat", back_populates="messages")

    def serialize(self) -> dict:
        import json
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "sender": self.sender.value,
            "type": self.type.value,
            "status": self.status.value,
            "content": self.content,
            "translation": self.translation,
            "media_url": self.media_url,
            "classification": json.loads(self.classification) if self.classification else None,
            "error": self.error,
            "timestamp": self.created_at.timestamp() * 1000,  # ms, matches your frontend's Date.now() convention
        }