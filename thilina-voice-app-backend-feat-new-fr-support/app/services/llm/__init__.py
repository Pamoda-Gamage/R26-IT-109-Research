"""LLM layer: pluggable transcription / translation / vision with automatic
Gemini <-> OpenAI failover, retry/backoff, a concurrency cap, and an in-process
response cache.

Public API (import from ``app.services.llm``):

    transcribe_audio(audio_bytes)        -> (transcript, translation)
    translate_text(text)                 -> (transcript, translation)
    analyze_image(image_bytes, mime, caption="") -> vision dict
    any_provider_available()             -> bool
    AllProvidersFailed, LLMError         -> exceptions
"""
from app.services.llm.base import (
    AllProvidersFailed,
    LLMError,
    LLMPermanent,
    LLMTransient,
)
from app.services.llm.client import (
    analyze_image,
    any_provider_available,
    transcribe_audio,
    translate_text,
)

# Back-compat alias — the old name used across chats.py.
analyze_image_v2 = analyze_image

__all__ = [
    "transcribe_audio",
    "translate_text",
    "analyze_image",
    "analyze_image_v2",
    "any_provider_available",
    "AllProvidersFailed",
    "LLMError",
    "LLMPermanent",
    "LLMTransient",
]
