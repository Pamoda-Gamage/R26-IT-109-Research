import os

from dotenv import load_dotenv

# Load backend/.env once, here, before anything reads os.getenv — every module
# imports `app.config`, so this is the single earliest point. (Previously only
# gemini_service loaded it, so .env overrides of the thresholds below were
# silently ignored unless the vars were also exported in the shell.)
load_dotenv()

# Below this, a classifier field is treated as "not confident enough" and can
# trigger a clarifying question instead of a final answer.
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))

# Urgency gets its own (stricter) gate: the local urgency head is poorly
# calibrated and over-predicts "high", so we ask a clarifying question unless
# the top prediction is both confident AND clearly ahead of the runner-up.
URGENCY_CONFIDENCE_THRESHOLD = float(os.getenv("URGENCY_CONFIDENCE_THRESHOLD", "0.60"))
URGENCY_MIN_MARGIN = float(os.getenv("URGENCY_MIN_MARGIN", "0.15"))

# How many clarifying-question rounds a single chat/case can go through
# before the system commits to a best-guess answer regardless of confidence.
MAX_CLARIFICATION_ROUNDS = int(os.getenv("MAX_CLARIFICATION_ROUNDS", "1"))


# ---------------------------------------------------------------------------
# LLM providers (transcription / translation / vision fallback)
# ---------------------------------------------------------------------------
# Which provider to try first. The other one is used as an automatic failover
# when LLM_FALLBACK_ENABLED is true (429 / quota / auth / model / 5xx errors).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
LLM_FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true"

# Max concurrent in-flight provider API calls (background tasks run in a
# threadpool, so a burst of uploads would otherwise hit the provider at once).
LLM_MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "3"))

# Number of cached transcription/translation/vision responses kept in-process
# (keyed by a hash of the input). 0 disables the cache.
LLM_CACHE_MAXSIZE = int(os.getenv("LLM_CACHE_MAXSIZE", "512"))

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")


# ---------------------------------------------------------------------------
# Image recognition (zero-shot CLIP primary + optional Gemini fallback)
# ---------------------------------------------------------------------------

# When true, an uncertain local (CLIP) image result is allowed to fall back to
# Gemini "to improvise". Set to false to run with zero Google dependency.
ENABLE_GEMINI_FALLBACK = os.getenv("ENABLE_GEMINI_FALLBACK", "true").lower() == "true"

# HuggingFace id of the CLIP checkpoint used as the frozen image encoder.
CLIP_MODEL_NAME = os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")

# When true (default), the CLIP model + prompt-bank matrices load on the first
# image request rather than at process startup — keeps `uvicorn` boot and
# text-only deploys unaffected, and lets the app start with no CLIP weights.
CLIP_LAZY_LOAD = os.getenv("CLIP_LAZY_LOAD", "true").lower() == "true"

# Below these, a head's zero-shot prediction is "not confident enough" and
# contributes a reason to fall back to Gemini.
IMAGE_OBJECT_TYPE_MIN_CONF = float(os.getenv("IMAGE_OBJECT_TYPE_MIN_CONF", "0.45"))
IMAGE_SUBTYPE_MIN_CONF = float(os.getenv("IMAGE_SUBTYPE_MIN_CONF", "0.35"))
IMAGE_SERVICE_TYPE_MIN_CONF = float(os.getenv("IMAGE_SERVICE_TYPE_MIN_CONF", "0.40"))

# Minimum gap between the top-1 and top-2 object_type probabilities; a smaller
# margin means the model is torn between two categories.
IMAGE_TOP2_MARGIN_MIN = float(os.getenv("IMAGE_TOP2_MARGIN_MIN", "0.08"))

# A condition tag is emitted when its pairwise probability against the
# "nothing wrong" anchor (softmax over [tag, anchor]) exceeds this.
IMAGE_CONDITION_THRESHOLD = float(os.getenv("IMAGE_CONDITION_THRESHOLD", "0.6"))
