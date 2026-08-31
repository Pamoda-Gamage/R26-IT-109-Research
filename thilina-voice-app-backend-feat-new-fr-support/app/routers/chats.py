"""
Chat/session REST API.

TODO Note : Need to implement true JWT user_id here to secure chat in production - Thilina
"""
import os

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session

from app import config
from app.database import get_db, SessionLocal
from app.models import Chat, Message, MessageSender, MessageType, MessageStatus
from app.schemas import CreateChatRequest, SendTextRequest
from app.connection_manager import manager
from app.services.llm import (
    transcribe_audio, translate_text, analyze_image_v2, any_provider_available,
    AllProvidersFailed, LLMError,
)

gemini_available = any_provider_available
from app.services.image_recognition_service import (
    recognize_image, should_fallback_to_gemini, reconcile,
)
from app.services.dispatch_service import (
    classify_and_respond, send_fallback_message, broadcast_sync, emit_stage,
)
from app.core.logger import logger

router = APIRouter()

MEDIA_DIR = os.getenv("MEDIA_DIR", "./media")
os.makedirs(MEDIA_DIR, exist_ok=True)


def get_chat_or_404(chat_id: str, db: Session) -> Chat:
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


_KNOWN_PROVIDERS = {"gemini", "openai"}


def _prefer(model: str | None) -> str | None:
    """Map the client's model/provider hint to an LLM primary-provider
    preference. Anything else ("auto", legacy ids like "lr-v1") -> None, i.e.
    use the server-configured default."""
    return model if model in _KNOWN_PROVIDERS else None


def _user_facing_error(exc: Exception) -> str:
    """Short, non-leaky text for the failed-message bubble. The raw provider
    error (which can be a bare `404 models/... not found` when the API key is
    wrong/expired) only goes to the logs."""
    if isinstance(exc, AllProvidersFailed):
        return ("The language service is temporarily unavailable or over capacity. "
                "Please resend your message in a moment.")
    if isinstance(exc, LLMError):
        return "We couldn't process that message right now — please try again."
    return "Something went wrong processing that message — please try again."


def _handle_processing_failure(db: Session, chat_id: str, message_id: str, exc: Exception) -> None:
    logger.exception("processing failed for message %s: %s", message_id, exc)
    friendly = _user_facing_error(exc)
    emit_stage(chat_id, message_id, "failed", "error", detail={"error": friendly})
    user_msg = db.query(Message).filter(Message.id == message_id).first()
    if user_msg:
        user_msg.status = MessageStatus.failed
        user_msg.error = friendly
        db.commit()
        broadcast_sync(chat_id, {"type": "message_update", "message": user_msg.serialize()})


#Chat (session) management

@router.post("/api/chats")
def create_chat(payload: CreateChatRequest, db: Session = Depends(get_db)):
    logger.info(
        "[cyan]Creating new chat[/cyan] for user [bold]%s[/bold]",
        payload.user_id,
    )

    chat = Chat(user_id=payload.user_id, title=payload.title or "New request")
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"id": chat.id, "title": chat.title, "status": chat.status.value}


@router.get("/api/chats")
def list_chats(user_id: str, db: Session = Depends(get_db)):
    """All chats/cases for a user — this is what powers a ChatGPT-style
    sidebar of past and ongoing requests."""
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return [
        {"id": c.id, "title": c.title, "status": c.status.value, "updated_at": c.updated_at.isoformat()}
        for c in chats
    ]


@router.get("/api/chats/{chat_id}/messages")
def get_messages(chat_id: str, db: Session = Depends(get_db)):
    chat = get_chat_or_404(chat_id, db)
    return [m.serialize() for m in chat.messages]


# ---------- Sending messages into a chat ----------

@router.post("/api/chats/{chat_id}/messages/text")
async def send_text(chat_id: str, payload: SendTextRequest, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db)):
    chat = get_chat_or_404(chat_id, db)

    # status=processing (not complete) — the text still needs a translation
    # pass before it's classifiable, same as audio's transcript/translation step.
    user_msg = Message(chat_id=chat.id, sender=MessageSender.user, type=MessageType.text,
                        content=payload.text, status=MessageStatus.processing)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    await manager.broadcast(chat_id, {"type": "message", "message": user_msg.serialize()})

    background_tasks.add_task(process_text_message, chat_id, user_msg.id, payload.model)
    return {"message_id": user_msg.id, "status": "processing"}


@router.post("/api/chats/{chat_id}/messages/audio")
async def send_audio(chat_id: str, background_tasks: BackgroundTasks,
                      file: UploadFile = File(...), model: str = Form(...),
                      db: Session = Depends(get_db)):
    chat = get_chat_or_404(chat_id, db)
    audio_bytes = await file.read()

    # Save immediately with status=processing so the UI can show "sent,
    # transcribing…" the instant it's posted, rather than only after the
    # (slow) Gemini round trip finishes.
    user_msg = Message(chat_id=chat.id, sender=MessageSender.user, type=MessageType.audio,
                        status=MessageStatus.processing)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    await manager.broadcast(chat_id, {"type": "message", "message": user_msg.serialize()})

    background_tasks.add_task(process_audio_message, chat_id, user_msg.id, audio_bytes, model)
    return {"message_id": user_msg.id, "status": "processing"}


@router.post("/api/chats/{chat_id}/messages/image")
async def send_image(chat_id: str, background_tasks: BackgroundTasks,
                      file: UploadFile = File(...), caption: str = Form(""),
                      db: Session = Depends(get_db)):
    """Field photo attached to an existing case (e.g. a photo of the damaged
    pipe/appliance). Stored as its own message so it threads inline with
    the rest of the conversation. The photo is always analyzed by the vision
    model, whether or not a caption was typed."""
    chat = get_chat_or_404(chat_id, db)
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    fname = f"{chat.id}-{Message().id}{ext}"  # fresh uuid for filename uniqueness
    fpath = os.path.join(MEDIA_DIR, fname)
    image_bytes = await file.read()
    with open(fpath, "wb") as f:
        f.write(image_bytes)
    mime_type = file.content_type or "image/jpeg"

    # status=processing — the photo still needs vision analysis before it's
    # classifiable, same as audio's transcript/translation step.
    user_msg = Message(
        chat_id=chat.id, sender=MessageSender.user, type=MessageType.image,
        content=caption or None, media_url=f"/media/{fname}",
        status=MessageStatus.processing,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    await manager.broadcast(chat_id, {"type": "message", "message": user_msg.serialize()})

    background_tasks.add_task(
        process_image_message, chat_id, user_msg.id, image_bytes, mime_type, caption.strip()
    )
    return {"message_id": user_msg.id, "status": "processing"}


# ---------- Background processing (runs after the HTTP response is sent) ----------

def process_text_message(chat_id: str, message_id: str, model: str | None = None):
    db = SessionLocal()
    try:
        user_msg = db.query(Message).filter(Message.id == message_id).first()
        emit_stage(chat_id, message_id, "translating", "start")
        transcript, translation = translate_text(user_msg.content or "", prefer=_prefer(model))
        emit_stage(chat_id, message_id, "translating", "done")
        # Normalise the typed text to Sinhala script where applicable, so the
        # bubble shows original + English just like a voice message.
        user_msg.content = transcript or user_msg.content
        user_msg.translation = translation
        user_msg.status = MessageStatus.complete
        db.commit()
        db.refresh(user_msg)
        broadcast_sync(chat_id, {"type": "message_update", "message": user_msg.serialize()})

        if translation:
            classify_and_respond(chat_id, db, message_id=message_id)
        else:
            send_fallback_message(
                chat_id, db,
                "Sorry, I did not understand. Please try again.",
                "සමාවෙන්න, මට තේරුණේ නැහැ. නැවත උත්සාහ කරන්න.",
            )

    except Exception as e:
        _handle_processing_failure(db, chat_id, message_id, e)
    finally:
        db.close()


def process_audio_message(chat_id: str, message_id: str, audio_bytes: bytes, model: str):
    db = SessionLocal()
    try:
        emit_stage(chat_id, message_id, "transcribing", "start")
        transcript, translation = transcribe_audio(audio_bytes, prefer=_prefer(model))
        emit_stage(chat_id, message_id, "transcribing", "done")

        user_msg = db.query(Message).filter(Message.id == message_id).first()
        user_msg.content = transcript
        user_msg.translation = translation
        user_msg.status = MessageStatus.complete
        db.commit()
        db.refresh(user_msg)
        broadcast_sync(chat_id, {"type": "message_update", "message": user_msg.serialize()})

        if translation:
            classify_and_respond(chat_id, db, message_id=message_id)
        else:
            send_fallback_message(
                chat_id, db,
                "Sorry, I did not understand. Please try again.",
                "සමාවෙන්න, මට තේරුණේ නැහැ. නැවත උත්සාහ කරන්න.",
            )

    except Exception as e:
        _handle_processing_failure(db, chat_id, message_id, e)
    finally:
        db.close()


def process_image_message(chat_id: str, message_id: str, image_bytes: bytes, mime_type: str, caption: str):
    db = SessionLocal()
    try:
        # Primary: self-hosted zero-shot CLIP recogniser (no Gemini).
        emit_stage(chat_id, message_id, "analysing_photo", "start")
        vision_result = recognize_image(image_bytes, caption)
        do_fallback, reasons = should_fallback_to_gemini(vision_result)
        if do_fallback and config.ENABLE_GEMINI_FALLBACK and gemini_available():
            logger.info("Image recognition falling back to Gemini: %s", reasons)
            emit_stage(chat_id, message_id, "analysing_photo", "start",
                       detail={"stage_note": "double-checking with Gemini"})
            try:
                gemini_result = analyze_image_v2(image_bytes, mime_type, caption)
                vision_result = reconcile(vision_result, gemini_result, reasons)
            except Exception as e:
                logger.warning("Gemini fallback failed, keeping CLIP result: %s", e)
                vision_result["fallback_reasons"] = reasons + ["gemini_call_failed"]

        description = vision_result.get("description", "")
        suggested_service_type = vision_result.get("suggested_service_type")
        emit_stage(chat_id, message_id, "analysing_photo", "done", detail={
            "object_type": vision_result.get("object_type"),
            "subtype": vision_result.get("subtype"),
            "recognition_source": vision_result.get("recognition_source"),
        })

        user_msg = db.query(Message).filter(Message.id == message_id).first()
        # Reuse the existing `translation` column for the image's English
        # description — this is what lets build_case_context() treat
        # text/audio/image user messages uniformly with no schema change.
        user_msg.translation = f"{caption}. {description}".strip(". ") if caption else description
        user_msg.status = MessageStatus.complete
        db.commit()
        db.refresh(user_msg)
        broadcast_sync(chat_id, {"type": "message_update", "message": user_msg.serialize()})

        if description:
            classify_and_respond(chat_id, db, vision_result=vision_result, message_id=message_id)
        else:
            send_fallback_message(
                chat_id, db,
                "Sorry, I couldn't analyze that photo. Please try again or add a description.",
                "සමාවෙන්න, ඒ ෆොටෝව විශ්ලේෂණය කරන්න බැරි වුණා. නැවත උත්සාහ කරන්න හෝ විස්තරයක් එකතු කරන්න.",
            )

    except Exception as e:
        _handle_processing_failure(db, chat_id, message_id, e)
    finally:
        db.close()