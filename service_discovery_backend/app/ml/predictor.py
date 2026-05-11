from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import re

import joblib
import numpy as np

from .train_model import train

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models_store"

HIGH_URGENCY_KEYWORDS = {"urgent", "emergency", "ikmanata", "now", "danger", "fire", "smoke", "accident", "leak", "spark", "thief", "help", "asap", "immediately"}
MODERATE_URGENCY_KEYWORDS = {"today", "soon", "quick", "within", "please", "important", "need"}
VISUAL_HINT_MAP = {
    "leak": "plumber", "pipe": "plumber", "tap": "plumber", "water": "plumber",
    "wire": "electrician", "switch": "electrician", "spark": "electrician", "plug": "electrician",
    "car": "mechanic", "bike": "mechanic", "engine": "mechanic", "tyre": "mechanic",
    "fire": "fire", "smoke": "fire", "flame": "fire",
    "injury": "hospital", "blood": "hospital", "medicine": "hospital",
}


def _ensure_models() -> None:
    if not (MODELS_DIR / "intent_classifier.joblib").exists() or not (MODELS_DIR / "urgency_classifier.joblib").exists():
        train()


class BehaviourAwarePredictor:
    def __init__(self) -> None:
        _ensure_models()
        self.intent_model = joblib.load(MODELS_DIR / "intent_classifier.joblib")
        self.urgency_model = joblib.load(MODELS_DIR / "urgency_classifier.joblib")
        self.training_report = joblib.load(MODELS_DIR / "training_report.joblib") if (MODELS_DIR / "training_report.joblib").exists() else {}

    @staticmethod
    def _probabilities(model: Any, text: str) -> Dict[str, float]:
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba([text])[0]
            classes = model.classes_
            return {str(c): round(float(p), 4) for c, p in zip(classes, probs)}
        return {}

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def predict(self, transcript: str, visual_hint: str | None = None, audio_features: Dict[str, float] | None = None) -> Dict[str, Any]:
        text = self._normalize_text(transcript)
        if not text:
            text = "unknown service request"

        intent = str(self.intent_model.predict([text])[0])
        urgency = str(self.urgency_model.predict([text])[0])
        intent_probs = self._probabilities(self.intent_model, text)
        urgency_probs = self._probabilities(self.urgency_model, text)

        tokens = set(re.findall(r"[a-zA-Z]+", text))
        keyword_hits = sorted(tokens.intersection(HIGH_URGENCY_KEYWORDS))
        if keyword_hits:
            urgency = "high"
        elif tokens.intersection(MODERATE_URGENCY_KEYWORDS) and urgency == "normal":
            urgency = "moderate"

        visual_adjustment = None
        if visual_hint:
            hint_text = self._normalize_text(visual_hint)
            for key, mapped_intent in VISUAL_HINT_MAP.items():
                if key in hint_text:
                    visual_adjustment = f"Visual context hint '{key}' reinforced service category '{mapped_intent}'."
                    intent = mapped_intent
                    break

        acoustic_adjustment = None
        if audio_features:
            rms = audio_features.get("rms", 0.0)
            peak = audio_features.get("peak", 0.0)
            zero_cross_rate = audio_features.get("zero_cross_rate", 0.0)
            if rms > 0.18 or peak > 0.75 or zero_cross_rate > 0.18:
                if urgency != "high":
                    urgency = "moderate"
                acoustic_adjustment = "Acoustic energy or speech dynamics increased urgency estimate."

        success_probability = self._estimate_success_probability(intent, urgency, intent_probs, urgency_probs)
        return {
            "transcript": transcript,
            "normalized_transcript": text,
            "intent": intent,
            "urgency": urgency,
            "intent_probabilities": intent_probs,
            "urgency_probabilities": urgency_probs,
            "keyword_hits": keyword_hits,
            "visual_adjustment": visual_adjustment,
            "acoustic_adjustment": acoustic_adjustment,
            "success_probability": success_probability,
            "training_report": self.training_report,
        }

    @staticmethod
    def _estimate_success_probability(intent: str, urgency: str, intent_probs: Dict[str, float], urgency_probs: Dict[str, float]) -> float:
        intent_conf = intent_probs.get(intent, max(intent_probs.values()) if intent_probs else 0.65)
        urgency_conf = urgency_probs.get(urgency, max(urgency_probs.values()) if urgency_probs else 0.6)
        urgency_penalty = {"normal": 0.02, "moderate": 0.06, "high": 0.10}.get(urgency, 0.05)
        probability = 0.52 + 0.30 * intent_conf + 0.20 * urgency_conf - urgency_penalty
        return round(float(np.clip(probability, 0.35, 0.98)), 4)


predictor = BehaviourAwarePredictor()
