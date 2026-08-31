"""Provider-agnostic contracts for the LLM path (transcription / translation /
image-recognition fallback).

Every provider raises one of the exceptions below so the dispatcher in
`client.py` can decide uniformly whether to retry, fail over, or give up:

- ``LLMTransient``  — retryable (429, 5xx, timeout, connection reset). The
  provider already retries these a few times with backoff before letting one
  escape; when it does, the dispatcher fails over to the next provider.
- ``LLMPermanent``  — not retryable on this provider (bad/expired key, unknown
  model, malformed request). The dispatcher fails over immediately.
- ``AllProvidersFailed`` — raised by the dispatcher when no provider succeeded.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Base class for every error the LLM layer surfaces to callers."""


class LLMTransient(LLMError):
    """A temporary failure — safe to retry / fail over (429, 5xx, timeout)."""


class LLMPermanent(LLMError):
    """A non-retryable failure for this provider (auth, unknown model, 4xx)."""


class AllProvidersFailed(LLMError):
    """No configured provider could complete the request."""

    def __init__(self, attempts: list[str]):
        self.attempts = attempts
        super().__init__("All LLM providers failed: " + "; ".join(attempts))


@runtime_checkable
class LLMProvider(Protocol):
    """The three operations the app needs from an LLM provider. Implementations
    live in ``gemini_provider.py`` / ``openai_provider.py``."""

    name: str

    def available(self) -> bool:
        """True when this provider has the credentials it needs to be tried."""

    def transcribe_audio(self, audio_bytes: bytes) -> tuple[str, str]:
        """Audio bytes -> (native-script transcript, English translation)."""

    def translate_text(self, text: str) -> tuple[str, str]:
        """Typed text -> (transcript normalised to native script, English translation)."""

    def analyze_image(self, image_bytes: bytes, mime_type: str, caption: str = "") -> dict:
        """Photo -> the same dict shape as
        ``image_recognition_service.recognize_image`` (minus internal score maps)."""
