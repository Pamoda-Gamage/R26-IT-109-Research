"""OpenAI implementation of the LLMProvider contract — the automatic failover
when Gemini is rate-limited or unavailable (and usable as the primary via
``LLM_PROVIDER=openai``).

Notes:
- translate / vision use Chat Completions in JSON mode with the *same* prompts
  as Gemini (see ``prompts.py``).
- audio needs two calls: Whisper for the native-script transcript, then
  ``translate_text`` for the English translation (the Whisper ``translations``
  endpoint only returns English and would lose the Sinhala-script transcript).
"""
from __future__ import annotations

import base64
import io
import json

from app import config
from app.core.logger import logger
from app.services.llm.base import LLMPermanent, LLMTransient
from app.services.llm.prompts import (
    RESCRIPT_PROMPT,
    TRANSLATE_PROMPT,
    build_vision_prompt,
    finalize_vision_result,
)
from app.services.llm.retry import with_retry


def _classify(exc: Exception) -> Exception:
    import openai

    if isinstance(exc, (openai.RateLimitError, openai.APITimeoutError,
                        openai.APIConnectionError, openai.InternalServerError)):
        return LLMTransient(f"openai {type(exc).__name__}: {exc}")
    if isinstance(exc, openai.APIStatusError):
        code = getattr(exc, "status_code", None)
        if isinstance(code, int) and code >= 500:
            return LLMTransient(f"openai {code}: {exc}")
        return LLMPermanent(f"openai {code}: {exc}")
    if isinstance(exc, openai.OpenAIError):
        return LLMPermanent(f"openai {type(exc).__name__}: {exc}")
    return LLMPermanent(f"openai {type(exc).__name__}: {exc}")


class OpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        self._client = None

    def _key(self) -> str:
        return config.OPENAI_API_KEY or ""

    def available(self) -> bool:
        return bool(self._key())

    def _get_client(self):
        if self._client is None:
            key = self._key()
            if not key:
                raise LLMPermanent("OPENAI_API_KEY not set")
            from openai import OpenAI
            self._client = OpenAI(api_key=key)
        return self._client

    @with_retry
    def _chat_json(self, system_prompt: str, user_content) -> tuple[dict, str]:
        try:
            resp = self._get_client().chat.completions.create(
                model=config.OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as e:
            raise _classify(e) from e

        raw = (resp.choices[0].message.content or "").strip()
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("expected a JSON object")
        except (json.JSONDecodeError, ValueError):
            logger.warning("OpenAI response was not valid JSON: %r", raw)
            parsed = {}
        return parsed, raw

    def translate_text(self, text: str) -> tuple[str, str]:
        parsed, raw = self._chat_json(TRANSLATE_PROMPT, text)
        transcript = parsed.get("transcript", "").strip() if parsed else ""
        translation = parsed.get("translation", "").strip() if parsed else ""
        return (transcript or text), translation

    def rescript_to_sinhala(self, text: str) -> str:
        """Rewrite a Devanagari/romanized transcript in Sinhala script (used by
        client._dispatch when the first pass still returned Devanagari)."""
        parsed, _ = self._chat_json(RESCRIPT_PROMPT, text)
        return (parsed.get("transcript", "").strip() if parsed else "") or text

    @with_retry
    def _transcribe(self, audio_bytes: bytes) -> str:
        buf = io.BytesIO(audio_bytes)
        buf.name = "audio.webm"
        try:
            tr = self._get_client().audio.transcriptions.create(
                model=config.OPENAI_TRANSCRIBE_MODEL,
                file=buf,
            )
        except Exception as e:
            raise _classify(e) from e
        return (getattr(tr, "text", "") or "").strip()

    def transcribe_audio(self, audio_bytes: bytes) -> tuple[str, str]:
        raw = self._transcribe(audio_bytes)
        if not raw:
            return "", ""
        # Whisper barely supports Sinhala (often romanizes or emits Devanagari).
        # The second call normalises the script AND gets the English translation;
        # keep the normalised transcript, not Whisper's raw output.
        normalised, translation = self.translate_text(raw)
        return (normalised or raw), translation

    def analyze_image(self, image_bytes: bytes, mime_type: str, caption: str = "") -> dict:
        data_uri = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
        user_content = [
            {"type": "text", "text": caption or "Analyse this photo."},
            {"type": "image_url", "image_url": {"url": data_uri}},
        ]
        parsed, raw = self._chat_json(build_vision_prompt(caption), user_content)
        result = finalize_vision_result(parsed, raw)
        result["llm_provider"] = self.name
        return result
