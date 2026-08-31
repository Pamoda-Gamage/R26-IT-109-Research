from sentence_transformers import SentenceTransformer
import json
import joblib
import os

from app import config
from app.core.logger import logger
from app.services.gemini_service import gemini_available

#Load models at start in singleton

EMBEDDER_NAME = "all-MiniLM-L6-v2"
embedder = SentenceTransformer(EMBEDDER_NAME)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/
MODEL_DIR = os.path.join(BASE_DIR, "models")

intent_clf = joblib.load(os.path.join(MODEL_DIR, "intent_classifier_lr.joblib"))
intent_encoder = joblib.load(os.path.join(MODEL_DIR, "intent_encoder_lr.joblib"))
service_clf = joblib.load(os.path.join(MODEL_DIR, "service_classifier_lr.joblib"))
service_encoder = joblib.load(os.path.join(MODEL_DIR, "service_encoder_lr.joblib"))
urgency_clf = joblib.load(os.path.join(MODEL_DIR, "urgency_classifier_lr.joblib"))
urgency_encoder = joblib.load(os.path.join(MODEL_DIR, "urgency_encoder_lr.joblib"))

# Ground truth label list, derived from the trained encoder so it can never
# drift from what the classifier actually knows about (used to constrain the
# vision model's service-type guess to the same closed vocabulary).
SERVICE_TYPE_LABELS: list[str] = list(service_encoder.classes_)


def _candidates(clf, encoder, proba, top: int | None = None) -> list[dict]:
    """Ranked {label, confidence} list for a classifier head, sorted desc.
    Maps through `clf.classes_` (not a raw positional zip with
    `encoder.classes_`) so this doesn't rely on LabelEncoder's contiguous-int
    behavior as an implicit contract."""
    labels = encoder.inverse_transform(clf.classes_)
    ranked = sorted(zip(labels, proba.tolist()), key=lambda x: -x[1])
    if top is not None:
        ranked = ranked[:top]
    return [{"label": label, "confidence": conf} for label, conf in ranked]


# Loaded once — a small JSON written next to the .joblib files by
# train_pipeline.py (training date, row counts, held-out metrics). Lets
# _model_info() surface which artifact is live so a stale model is detectable.
def _load_model_card() -> dict:
    try:
        with open(os.path.join(MODEL_DIR, "model_card.json"), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


_MODEL_CARD = _load_model_card()

# Curated, conservative emergency keywords. These can only ever RAISE a
# prediction to "high" (never lower one) — a safety net for the cases where a
# wrong "low"/"medium" is genuinely dangerous. Every override is logged.
_EMERGENCY_KEYWORDS = (
    "collapsed", "unconscious", "not breathing", "can't breathe", "cant breathe",
    "chest pain", "heart attack", "stroke", "seizure", "bleeding heavily",
    "fire", "on fire", "gas leak", "smell of gas", "smell gas",
    "electric shock", "electrocuted", "sparking", "burning smell",
    "flooding", "flooded", "burst pipe", "water everywhere", "gushing",
    "trapped", "accident", "emergency",
)


def _apply_urgency_guardrail(urgency_label: str, text: str) -> tuple[str, str | None]:
    """Returns (label, override_reason|None)."""
    if urgency_label == "high":
        return urgency_label, None
    lowered = (text or "").lower()
    for kw in _EMERGENCY_KEYWORDS:
        if kw in lowered:
            return "high", f"emergency keyword {kw!r}"
    return urgency_label, None


def _model_info() -> dict:
    return {
        "embedder": EMBEDDER_NAME,
        "classifier": "logistic_regression",
        "vision_primary": config.CLIP_MODEL_NAME,
        "vision_fallback": config.GEMINI_MODEL if gemini_available() else None,
        "model_card": _MODEL_CARD or None,
    }


def predict(text: str, urgency_text: str | None = None):
    """Classify a dispatch case.

    `text` is the full case narrative (all messages so far) — context helps
    decide *what* service and intent this is.

    `urgency_text` (defaults to `text`) is what the urgency head sees. Callers
    pass just the latest user message here: urgency is a property of the
    current ask, and the local urgency model was trained on single short
    utterances — feeding it the whole concatenated history skews it to "high".
    """
    urgency_src = urgency_text if urgency_text is not None else text

    vector = embedder.encode([text])
    urgency_vector = vector if urgency_src == text else embedder.encode([urgency_src])

    intent_prediction = intent_clf.predict(vector)[0]
    service_prediction = service_clf.predict(vector)[0]
    urgency_prediction = urgency_clf.predict(urgency_vector)[0]

    intent_probability = intent_clf.predict_proba(vector)[0]
    service_probability = service_clf.predict_proba(vector)[0]
    urgency_probability = urgency_clf.predict_proba(urgency_vector)[0]

    intent_label = intent_encoder.inverse_transform([intent_prediction])[0]
    service_label = service_encoder.inverse_transform([service_prediction])[0]
    urgency_label = urgency_encoder.inverse_transform([urgency_prediction])[0]

    guarded_label, override_reason = _apply_urgency_guardrail(urgency_label, urgency_src)
    if override_reason:
        logger.warning("urgency guardrail: %s -> high (%s)", urgency_label, override_reason)
        urgency_label = guarded_label

    return {
        "intent": intent_label,
        "intent_confidence": float(intent_probability.max()),
        "intent_candidates": _candidates(intent_clf, intent_encoder, intent_probability),
        "service_type": service_label,
        "service_confidence": float(service_probability.max()),
        "service_candidates": _candidates(service_clf, service_encoder, service_probability, top=5),
        "urgency": urgency_label,
        "urgency_confidence": float(urgency_probability.max()),
        "urgency_candidates": _candidates(urgency_clf, urgency_encoder, urgency_probability),
        "urgency_override": override_reason,
        "model_info": _model_info(),
    }

if __name__ == "__main__":
    examples = [
        "the toilet is clogged",
        "someone has collapsed",
        "i need a plumber immediately",
        "my ac is not working",
    ]
    for text in examples:
        result = predict(text)
        print(f"{text!r} -> {result}")



