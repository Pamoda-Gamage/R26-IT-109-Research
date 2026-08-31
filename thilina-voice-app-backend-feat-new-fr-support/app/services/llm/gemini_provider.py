"""Google Gemini implementation of the LLMProvider contract.

This is the code that used to live directly in ``app.services.gemini_service``;
it now sits behind the failover dispatcher in ``client.py``.
"""
from __future__ import annotations

import json
import os

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from app import config
from app.core.logger import logger
from app.services.llm.base import LLMPermanent, LLMTransient
from app.services.llm.prompts import (
    RESCRIPT_PROMPT,
    TRANSCRIBE_PROMPT,
    TRANSLATE_PROMPT,
    build_vision_prompt,
    finalize_vision_result,
)
from app.services.llm.retry import with_retry


def _classify(exc: Exception) -> Exception:
    """Map a google-genai error onto our transient/permanent split."""
    if isinstance(exc, genai_errors.APIError):
        code = getattr(exc, "code", None)
        if code == 429 or (isinstance(code, int) and code >= 500):
            return LLMTransient(f"gemini {code}: {getattr(exc, 'message', exc)}")
        return LLMPermanent(f"gemini {code}: {getattr(exc, 'message', exc)}")
    # httpx/requests connection & timeout errors surface as their own types
    name = type(exc).__name__.lower()
    if "timeout" in name or "connect" in name:
        return LLMTransient(f"gemini {type(exc).__name__}: {exc}")
    return LLMPermanent(f"gemini {type(exc).__name__}: {exc}")


class GeminiProvider:
    name = "gemini"

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    def available(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    def _get_client(self) -> genai.Client:
        if self._client is None:
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise LLMPermanent("GEMINI_API_KEY not set")
            self._client = genai.Client(api_key=key)
        return self._client

    @with_retry
    def _generate_json(self, contents: list) -> tuple[dict, str]:
        try:
            response = self._get_client().models.generate_content(
                model=config.GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
        except genai_errors.APIError as e:
            raise _classify(e) from e
        except Exception as e:  # connection/timeout/etc.
            raise _classify(e) from e

        raw = (response.text or "").strip()
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("expected a JSON object")
        except (json.JSONDecodeError, ValueError):
            logger.warning("Gemini response was not valid JSON: %r", raw)
            parsed = {}
        return parsed, raw

    def transcribe_audio(self, audio_bytes: bytes) -> tuple[str, str]:
        parsed, raw = self._generate_json([
            TRANSCRIBE_PROMPT,
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm"),
        ])
        transcript = parsed.get("transcript", "").strip() if parsed else raw
        translation = parsed.get("translation", "").strip() if parsed else ""
        return transcript, translation

    def translate_text(self, text: str) -> tuple[str, str]:
        parsed, raw = self._generate_json([TRANSLATE_PROMPT, text])
        transcript = parsed.get("transcript", "").strip() if parsed else ""
        translation = parsed.get("translation", "").strip() if parsed else ""
        return (transcript or text), translation

    def rescript_to_sinhala(self, text: str) -> str:
        """Rewrite a Devanagari/romanized transcript in Sinhala script (used by
        client._dispatch when the first pass still returned Devanagari)."""
        parsed, _ = self._generate_json([RESCRIPT_PROMPT, text])
        return (parsed.get("transcript", "").strip() if parsed else "") or text

    def analyze_image(self, image_bytes: bytes, mime_type: str, caption: str = "") -> dict:
        parsed, raw = self._generate_json([
            build_vision_prompt(caption),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ])
        result = finalize_vision_result(parsed, raw)
        result["llm_provider"] = self.name
        return result
