"""
Shared classification orchestration for text/audio/image messages.

Centralizes what used to be duplicated between process_text_message and
process_audio_message in routers/chats.py: building the case context,
running the classifier, deciding whether the result is confident enough to
commit to, and constructing the assistant's reply message.
"""
import asyncio
import json
import time

from sqlalchemy.orm import Session

from app.config import (
    CONFIDENCE_THRESHOLD, MAX_CLARIFICATION_ROUNDS, IMAGE_SUBTYPE_MIN_CONF,
    IMAGE_OBJECT_TYPE_MIN_CONF, IMAGE_SERVICE_TYPE_MIN_CONF, IMAGE_TOP2_MARGIN_MIN,
    URGENCY_CONFIDENCE_THRESHOLD, URGENCY_MIN_MARGIN,
)
from app.connection_manager import manager
from app.models import Message, MessageSender, MessageType, MessageStatus
from app.services.predict_service import predict
from app.services.urgency_rules import resolve_urgency_from_clarifying_answer
from app.services.image_taxonomy import (
    service_type_for_subtype, humanize, subtype_si, SUBTYPE_LABELS,
)
from app.core.logger import logger

# Above this the text classifier's service_type is trusted enough that a
# photo-derived subtype disagreement does NOT trigger a clarifying question.
_TEXT_SERVICE_TRUST = 0.75

FALLBACK_REPLY_EN = "Got it — here's what I found for your request."
FALLBACK_REPLY_SI = "හරි — ඔබේ ඉල්ලීම සඳහා මට හම්බ වූ දේ මෙන්න."


def broadcast_sync(chat_id: str, payload: dict):
    """Broadcast from a *sync* context (background tasks run in a threadpool
    with no running event loop), so we spin up a short-lived one."""
    asyncio.run(manager.broadcast(chat_id, payload))


# Ordered pipeline stages the frontend renders as a progress stepper. "matching"
# is intentionally absent — there is no provider-matching step yet.
STAGES = ("transcribing", "translating", "analysing_photo",
          "understanding", "classifying", "finalising")


def emit_stage(chat_id: str, message_id: str | None, stage: str,
               state: str = "start", detail: dict | None = None):
    """Broadcast a lightweight '{"type":"stage"}' event so the client can show
    what the backend is doing right now. Additive/non-breaking — clients that
    don't know the type ignore it. The last non-terminal stage is cached on the
    ConnectionManager so a reconnecting tab can catch up (see websocket.py)."""
    payload = {
        "type": "stage", "chat_id": chat_id, "message_id": message_id,
        "stage": stage, "state": state, "detail": detail,
        "ts": int(time.time() * 1000),
    }
    if stage == "failed" or (stage == "finalising" and state == "done"):
        manager.clear_stage(chat_id)
    else:
        manager.set_stage(chat_id, payload)
    broadcast_sync(chat_id, payload)


def build_case_context(chat_id: str, db: Session) -> str:
    """Concatenates every user message's best-available text for this chat
    (translated audio, typed text, image description) into one narrative —
    a chat is one dispatch case, so a follow-up answer should be classified
    together with everything said earlier in it, not in isolation."""
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.sender == MessageSender.user)
        .order_by(Message.created_at)
        .all()
    )
    parts = [m.translation or m.content for m in messages if (m.translation or m.content)]
    return "\n".join(parts)


def latest_user_message_text(chat_id: str, db: Session) -> str:
    """The most recent user message's best-available text (translated audio,
    typed text, or image description). This is what the urgency head is scored
    on — urgency is about the current ask, not the whole case history, and the
    local urgency model was trained on single short utterances."""
    latest = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.sender == MessageSender.user)
        .order_by(Message.created_at.desc())
        .first()
    )
    if not latest:
        return ""
    return (latest.translation or latest.content or "").strip()


def _count_clarification_rounds(chat_id: str, db: Session) -> int:
    assistant_messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.sender == MessageSender.assistant)
        .all()
    )
    rounds = 0
    for m in assistant_messages:
        if not m.classification:
            continue
        try:
            if json.loads(m.classification).get("needs_clarification"):
                rounds += 1
        except json.JSONDecodeError:
            continue
    return rounds


def _previous_clarification_reason(chat_id: str, db: Session) -> str | None:
    """Which check drove the most recent clarifying question (`service` /
    `urgency` / `intent` / a vision reason), so the current turn — the user's
    answer to it — knows what it is responding to. None for older assistant
    messages that predate the `clarification_reason` field."""
    latest = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.sender == MessageSender.assistant)
        .order_by(Message.created_at.desc())
        .first()
    )
    if not latest or not latest.classification:
        return None
    try:
        c = json.loads(latest.classification)
    except json.JSONDecodeError:
        return None
    if not c.get("needs_clarification"):
        return None
    return c.get("clarification_reason")


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _lowercase_first(text: str) -> str:
    """Lowercases the first letter for mid-sentence splicing, but leaves the
    standalone pronoun "I" alone — always capitalized in English regardless
    of sentence position."""
    if text.split(" ", 1)[0] == "I":
        return text
    return text[:1].lower() + text[1:]


def _latest_user_message_type(chat_id: str, db: Session) -> str | None:
    latest = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.sender == MessageSender.user)
        .order_by(Message.created_at.desc())
        .first()
    )
    return latest.type.value if latest else None


# Two phrasings per failing check — round 0 uses the plain version, any
# later round uses the second so consecutive turns can never repeat
# verbatim (a byte-identical follow-up question reads as a broken bot).
_QUESTION_TEMPLATES = {
    "service": [
        "Could you tell me a bit more about what kind of service you need?",
        "I still need a bit more to go on — what exactly needs fixing or attention here?",
    ],
    "urgency": [
        "How urgent is this — does it need help right away, or can it wait?",
        "One more check — is this urgent right now, or can it wait a bit?",
    ],
    "intent": [
        "Just to confirm — are you requesting a service, reporting an issue, or is this an emergency?",
        "Sorry, still not fully sure — is this a service request, an issue report, or an emergency?",
    ],
}

# Sinhala counterparts of _QUESTION_TEMPLATES, same keys/tiers — kept as a
# separate parallel dict (rather than tuples) so each language stays easy to
# scan/edit on its own.
_QUESTION_TEMPLATES_SI = {
    "service": [
        "ඔබට අවශ්‍ය සේවාව මොනවාද කියලා තව ටිකක් විස්තර කරන්න පුළුවන්ද?",
        "තවමත් මට හරියටම තේරෙන්නේ නැහැ — හරියටම මොකක්ද අලුත්වැඩියා කරන්න ඕන හෝ බලන්න ඕන දේ?",
    ],
    "urgency": [
        "මේක කොච්චර හදිසිද — දැන්ම උදව් ඕනද, නැත්නම් පොඩ්ඩක් ඉන්න පුළුවන්ද?",
        "තව එක දෙයක් අහන්නම් — මේක දැන් හදිසියිද, නැත්නම් ටිකක් ඉන්න පුළුවන්ද?",
    ],
    "intent": [
        "තහවුරු කරගන්න විතරයි — ඔබ සේවාවක් ඉල්ලනවාද, ගැටලුවක් වාර්තා කරනවාද, නැත්නම් මේක හදිසි අවස්ථාවක්ද?",
        "සමාවෙන්න, තවමත් මට හරියටම විශ්වාස නැහැ — මේක සේවා ඉල්ලීමක්ද, ගැටලු වාර්තාවක්ද, නැත්නම් හදිසි අවස්ථාවක්ද?",
    ],
}

# Sinhala labels for the closed service_type vocabulary the classifier was
# trained on (app/training/dataset_with_index.csv). Falls back to the raw
# English label for anything not listed here, so a future/unknown label
# degrades gracefully instead of raising.
_SERVICE_TYPE_SI = {
    "air_condition_technician": "ඒසී තාක්ෂණිකයා",
    "ambulance_service": "ගිලන්රථ සේවාව",
    "appliance_repair_service": "උපකරණ අලුත්වැඩියා සේවාව",
    "battery_jump_start_service": "බැටරි ජම්ප් ස්ටාර්ට් සේවාව",
    "car_care": "කාර් රැකවරණය",
    "carpenter": "වඩුකාරයා",
    "cctv_installer": "CCTV සවි කරන්නා",
    "cleaning_service": "පිරිසිදු කිරීමේ සේවාව",
    "computer_repair_service": "පරිගණක අලුත්වැඩියා සේවාව",
    "electrician": "විදුලි කාර්මිකයා",
    "gardner": "උයන්පල්ලා",
    "hospital_service": "රෝහල් සේවාව",
    "laptop_repair": "ලැප්ටොප් අලුත්වැඩියාව",
    "locksmith": "යතුරු පණ්ඩිතයා",
    "mason": "ගොඩනැගිලි කාර්මිකයා",
    "mechanic": "මිස්ත්‍රි",
    "mobile_phone_repair": "ජංගම දුරකථන අලුත්වැඩියාව",
    "movers": "ගෙදර මාරු කිරීමේ සේවාව",
    "network_operator": "ජාල ක්‍රියාකරු",
    "nursing_assistance": "හෙදියා සහාය",
    "painter": "සායම්කරු",
    "pest_controller": "පළිබෝධ පාලකයා",
    "plumber": "නළ කාර්මිකයා",
    "request_service": "සේවා ඉල්ලීම",
    "solar_technician": "සූර්ය බල තාක්ෂණිකයා",
    "tv_repair": "රූපවාහිනී අලුත්වැඩියාව",
    "water_pump_repair_service": "ජල පොම්ප අලුත්වැඩියා සේවාව",
}


def _service_type_si(label: str) -> str:
    return _SERVICE_TYPE_SI.get(label, label.replace("_", " "))


_MISMATCH_TEMPLATES_EN = [
    "Just to double check — the photo looks like it might be about {article} "
    "{vision_label}, but your message points to {service_type}. Which one is it?",
    "I want to get this right — is it really {service_type}, or is it more about "
    "{article} {vision_label} like the photo suggests?",
]

_MISMATCH_TEMPLATES_SI = [
    "දෙපාරක් හරිද බලමු — ෆොටෝවෙන් පේන්නේ {vision_label} වගේ, නමුත් ඔබේ පණිවිඩයෙන් "
    "පේන්නේ {service_type} කියලා. හරියටම මොකක්ද?",
    "මට හරියටම තේරුම් ගන්න ඕන — මේක ඇත්තටම {service_type} ද, නැත්නම් ෆොටෝවෙන් "
    "පේන විදිහට {vision_label} එකක්ද?",
]

# Photo shows a confidently-identified object whose usual service differs from
# what the text points to (e.g. photo of a fridge, text sounds like "mechanic").
_OBJECT_MISMATCH_TEMPLATES_EN = [
    "Just to check — the photo looks like {article} {vision_label}, but your "
    "message sounds like {service_type}. Which is it?",
    "I want to route this right — is it {service_type}, or is it more about "
    "{article} {vision_label} like the photo shows?",
]
_OBJECT_MISMATCH_TEMPLATES_SI = [
    "පොඩ්ඩක් බලමු — ෆොටෝවෙන් පේන්නේ {vision_label}ක් වගේ, නමුත් ඔබේ පණිවිඩයෙන් "
    "පේන්නේ {service_type} කියලා. හරියටම මොකක්ද?",
    "මට හරියට යොමු කරන්න ඕන — මේක {service_type}ද, නැත්නම් ෆොටෝවේ විදිහට {vision_label}ක්ද?",
]

# Photo is clearly of some object_type but the specific kind is unresolved —
# and getting it wrong matters for routing (a lorry job must not go to a
# car-only mechanic), so ask the user to pin it down.
_SUBTYPE_UNRESOLVED_TEMPLATES_EN = [
    "Thanks for the photo — to send the right person, is this for {options}?",
    "One detail so I route it right — which is it exactly: {options}?",
]
_SUBTYPE_UNRESOLVED_TEMPLATES_SI = [
    "ෆොටෝවට ස්තූතියි — හරි කෙනෙක් එවන්න, මේක {options}ද?",
    "හරියට යොමු කරන්න එක් විස්තරයක් — හරියටම මොකක්ද: {options}?",
]

# Curated "which kind is it?" option lists per object_type (EN, SI). Anything
# not listed falls back to the first few subtype labels for that object_type.
_SUBTYPE_OPTIONS = {
    "vehicle": (
        "a car, a van, a motorcycle, a three-wheeler, or a lorry/truck",
        "කාර් එකක්ද, වෑන් එකක්ද, මෝටර් සයිකලයක්ද, ත්‍රිරෝද රථයක්ද, නැත්නම් ලොරියක්",
    ),
    "appliance": (
        "a fridge, a washing machine, an air conditioner, or a water pump",
        "ශීතකරණයක්ද, රෙදි සෝදන යන්ත්‍රයක්ද, වායු සමීකරණයක්ද, නැත්නම් ජල පොම්පයක්",
    ),
    "electronic_device": (
        "a laptop, a desktop computer, a phone, or a TV",
        "ලැප්ටොප් එකක්ද, පරිගණකයක්ද, දුරකථනයක්ද, නැත්නම් රූපවාහිනියක්",
    ),
}


def _subtype_options(object_type: str | None) -> tuple[str, str]:
    if object_type in _SUBTYPE_OPTIONS:
        return _SUBTYPE_OPTIONS[object_type]
    subs = SUBTYPE_LABELS.get(object_type or "", [])[:4]
    joined = ", ".join(f"{_article(humanize(s))} {humanize(s)}" for s in subs) or "one of a few kinds"
    return joined, joined


def _clarification_reason(prediction: dict, mismatch: bool, object_mismatch: bool,
                          subtype_unresolved: bool) -> str:
    """Which failing check drives the clarifying question. Persisted on the
    stored classification (`clarification_reason`) so the *next* turn — the
    user's answer — knows what it is responding to (see
    `_previous_clarification_reason`)."""
    if mismatch:
        return "mismatch"
    if object_mismatch:
        return "object_mismatch"
    if subtype_unresolved:
        return "subtype_unresolved"
    _u_cands = prediction.get("urgency_candidates") or []
    _u_margin = (
        _u_cands[0]["confidence"] - _u_cands[1]["confidence"]
        if len(_u_cands) >= 2 else 1.0
    )
    if prediction["service_confidence"] < CONFIDENCE_THRESHOLD:
        return "service"
    if not prediction.get("urgency_override") and (
        prediction["urgency_confidence"] < URGENCY_CONFIDENCE_THRESHOLD
        or _u_margin < URGENCY_MIN_MARGIN
    ):
        return "urgency"
    return "intent"


def _build_clarifying_question(prediction: dict, mismatch: bool,
                                object_mismatch: bool, subtype_unresolved: bool,
                                vision: dict,
                                vision_suggested_service_type: str | None,
                                round_index: int, latest_is_image: bool,
                                reason: str) -> tuple[str, str]:
    """Returns (question_en, question_si) — the same question phrased in
    both languages, since Sinhala-only speakers otherwise can't read a
    clarifying follow-up written purely in English. `reason` is the value from
    `_clarification_reason` and selects the template for the non-vision path."""
    tier = min(round_index, 1)  # only two phrasings exist per check, cap the index

    if mismatch:
        # Mismatch only fires right after a photo was analyzed, so it
        # already references "the photo" directly — no separate ack needed.
        vision_label_en = vision_suggested_service_type.replace("_", " ")
        vision_label_si = _service_type_si(vision_suggested_service_type)
        service_type_en = prediction["service_type"].replace("_", " ")
        service_type_si = _service_type_si(prediction["service_type"])
        question_en = _MISMATCH_TEMPLATES_EN[tier].format(
            article=_article(vision_label_en), vision_label=vision_label_en,
            service_type=service_type_en,
        )
        question_si = _MISMATCH_TEMPLATES_SI[tier].format(
            vision_label=vision_label_si, service_type=service_type_si,
        )
        return question_en, question_si

    if object_mismatch:
        subtype = vision.get("subtype")
        vision_label_en = humanize(subtype)
        vision_label_si = subtype_si(subtype)
        service_type_en = prediction["service_type"].replace("_", " ")
        service_type_si = _service_type_si(prediction["service_type"])
        question_en = _OBJECT_MISMATCH_TEMPLATES_EN[tier].format(
            article=_article(vision_label_en), vision_label=vision_label_en,
            service_type=service_type_en,
        )
        question_si = _OBJECT_MISMATCH_TEMPLATES_SI[tier].format(
            vision_label=vision_label_si, service_type=service_type_si,
        )
        return question_en, question_si

    if subtype_unresolved:
        opt_en, opt_si = _subtype_options(vision.get("object_type"))
        return (
            _SUBTYPE_UNRESOLVED_TEMPLATES_EN[tier].format(options=opt_en),
            _SUBTYPE_UNRESOLVED_TEMPLATES_SI[tier].format(options=opt_si),
        )

    # `reason` is one of "service" / "urgency" / "intent" here (the vision
    # reasons return earlier via their bool params).
    key = reason if reason in _QUESTION_TEMPLATES else "intent"
    question_en = _QUESTION_TEMPLATES[key][tier]
    question_si = _QUESTION_TEMPLATES_SI[key][tier]

    if latest_is_image:
        question_en = f"Thanks for the photo — {_lowercase_first(question_en)}"
        question_si = f"ෆොටෝවට ස්තූතියි — {question_si}"
    return question_en, question_si


def classify_and_respond(chat_id: str, db: Session,
                          vision_result: dict | None = None,
                          vision_suggested_service_type: str | None = None,
                          message_id: str | None = None) -> Message:
    """The single entry point process_text_message/process_audio_message/
    process_image_message all call once their user message's translated
    text is persisted. Runs the classifier over the whole case so far,
    decides whether to ask a clarifying question or commit to an answer,
    and creates+broadcasts the assistant's reply message.

    `vision_result` is the full dict from image_recognition_service.recognize_image
    (or the Gemini fallback) for image messages; `vision_suggested_service_type`
    is kept for back-compat and is derived from it when not passed explicitly."""
    vision = vision_result or {}
    if vision_suggested_service_type is None:
        vision_suggested_service_type = vision.get("suggested_service_type")

    emit_stage(chat_id, message_id, "understanding", "start")
    case_text = build_case_context(chat_id, db)
    latest_text = latest_user_message_text(chat_id, db)
    urgency_text = latest_text or case_text

    emit_stage(chat_id, message_id, "classifying", "start")
    prediction = predict(case_text, urgency_text=urgency_text)

    # If this turn is the user's answer to the "how urgent is this?" clarifying
    # question, their words beat the (miscalibrated, single-utterance) urgency
    # head. Skip when an emergency keyword already forced "high".
    if _previous_clarification_reason(chat_id, db) == "urgency" and not str(
        prediction.get("urgency_override") or ""
    ).startswith("emergency keyword"):
        resolved = resolve_urgency_from_clarifying_answer(latest_text)
        if resolved and resolved != prediction["urgency"]:
            logger.info(
                "urgency resolved from clarifying answer: %s -> %s",
                prediction["urgency"], resolved,
            )
            prediction["urgency"] = resolved
            prediction["urgency_confidence"] = 1.0
            prediction["urgency_override"] = f"clarifying answer -> {resolved}"
            prediction["urgency_resolved_from_answer"] = True

    low_intent = prediction["intent_confidence"] < CONFIDENCE_THRESHOLD
    low_service = prediction["service_confidence"] < CONFIDENCE_THRESHOLD
    # Urgency gets a stricter gate: confident AND clearly ahead of the
    # runner-up. An emergency-keyword override always counts as confident.
    _urgency_cands = prediction.get("urgency_candidates") or []
    _urgency_margin = (
        _urgency_cands[0]["confidence"] - _urgency_cands[1]["confidence"]
        if len(_urgency_cands) >= 2 else 1.0
    )
    low_urgency = not prediction.get("urgency_override") and (
        prediction["urgency_confidence"] < URGENCY_CONFIDENCE_THRESHOLD
        or _urgency_margin < URGENCY_MIN_MARGIN
    )
    mismatch = bool(
        vision_suggested_service_type
        and vision_suggested_service_type != prediction["service_type"]
    )

    # Photo-derived checks (image messages only). These are what let a future
    # matching step avoid, e.g., sending a lorry mechanic to a car job.
    subtype = vision.get("subtype")
    subtype_conf = vision.get("subtype_confidence", 0.0)
    subtype_service = service_type_for_subtype(subtype)
    text_trusted = prediction["service_confidence"] >= _TEXT_SERVICE_TRUST

    object_mismatch = bool(
        vision and not mismatch and subtype and subtype_conf >= IMAGE_SUBTYPE_MIN_CONF
        and subtype_service and subtype_service != prediction["service_type"]
        and not text_trusted
    )
    subtype_unresolved = bool(
        vision and not mismatch and not object_mismatch
        and vision.get("object_type") not in (None, "other")
        and (not subtype or subtype_conf < IMAGE_SUBTYPE_MIN_CONF)
        and not text_trusted
    )

    rounds_used = _count_clarification_rounds(chat_id, db)
    needs_clarification = (
        low_intent or low_service or low_urgency
        or mismatch or object_mismatch or subtype_unresolved
    ) and (rounds_used < MAX_CLARIFICATION_ROUNDS)

    clarification_reason = (
        _clarification_reason(prediction, mismatch, object_mismatch, subtype_unresolved)
        if needs_clarification else None
    )

    prediction["needs_clarification"] = needs_clarification
    prediction["clarification_reason"] = clarification_reason
    prediction["vision_suggested_service_type"] = vision_suggested_service_type
    prediction["clarification_round"] = rounds_used
    # What gate thresholds/limits produced this result — lets a researcher see
    # e.g. "this hit the round cap and committed despite low confidence".
    prediction["confidence_thresholds"] = {
        "intent_service": CONFIDENCE_THRESHOLD,
        "urgency": URGENCY_CONFIDENCE_THRESHOLD,
        "urgency_min_margin": URGENCY_MIN_MARGIN,
    }
    prediction["urgency_classified_on"] = "latest_message"
    prediction["clarification_limits"] = {"used": rounds_used, "max": MAX_CLARIFICATION_ROUNDS}
    if vision:
        prediction["vision_object_type"] = vision.get("object_type")
        prediction["vision_subtype"] = subtype
        prediction["vision_subtype_confidence"] = subtype_conf
        prediction["vision_conditions"] = vision.get("conditions")
        prediction["vision_service_type"] = vision.get("service_type")
        prediction["recognition_source"] = vision.get("recognition_source")
        prediction["fallback_reasons"] = vision.get("fallback_reasons")
        # Previously computed by image_recognition_service but silently
        # dropped before reaching the frontend — forward for research display.
        prediction["vision_object_type_confidence"] = vision.get("object_type_confidence")
        prediction["vision_object_type_top2_margin"] = vision.get("object_type_top2_margin")
        prediction["vision_service_type_confidence"] = vision.get("service_type_confidence")
        prediction["vision_condition_scores"] = vision.get("condition_scores")
        prediction["vision_description"] = vision.get("description")
        prediction["vision_object_type_candidates"] = vision.get("object_type_candidates")
        prediction["vision_subtype_candidates"] = vision.get("subtype_candidates")
        prediction["vision_service_type_candidates"] = vision.get("service_type_candidates")
        prediction["confidence_thresholds"].update({
            "image_object_type": IMAGE_OBJECT_TYPE_MIN_CONF,
            "image_subtype": IMAGE_SUBTYPE_MIN_CONF,
            "image_service_type": IMAGE_SERVICE_TYPE_MIN_CONF,
            "image_top2_margin": IMAGE_TOP2_MARGIN_MIN,
        })

    emit_stage(chat_id, message_id, "finalising", "start",
               detail={"needs_clarification": needs_clarification})
    content, translation = (
        _build_clarifying_question(
            prediction, mismatch, object_mismatch, subtype_unresolved, vision,
            vision_suggested_service_type,
            round_index=rounds_used, latest_is_image=_latest_user_message_type(chat_id, db) == "image",
            reason=clarification_reason or "intent",
        )
        if needs_clarification
        else (FALLBACK_REPLY_EN, FALLBACK_REPLY_SI)
    )

    assistant_msg = Message(
        chat_id=chat_id, sender=MessageSender.assistant, type=MessageType.text,
        content=content, translation=translation,
        classification=json.dumps(prediction), status=MessageStatus.complete,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    emit_stage(chat_id, message_id, "finalising", "done")
    broadcast_sync(chat_id, {"type": "message", "message": assistant_msg.serialize()})
    return assistant_msg


def send_fallback_message(chat_id: str, db: Session, text_en: str, text_si: str) -> Message:
    """For the 'couldn't extract any usable text' cases (empty translation,
    empty image description) — no classification attempted."""
    assistant_msg = Message(
        chat_id=chat_id, sender=MessageSender.assistant, type=MessageType.text,
        content=text_en, translation=text_si, status=MessageStatus.complete,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    manager.clear_stage(chat_id)
    broadcast_sync(chat_id, {"type": "message", "message": assistant_msg.serialize()})
    return assistant_msg
