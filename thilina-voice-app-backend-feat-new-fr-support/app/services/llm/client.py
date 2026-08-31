"""Failover dispatcher — the public face of the LLM layer.

``chats.py`` imports ``transcribe_audio`` / ``translate_text`` / ``analyze_image``
from here (same names the old ``gemini_service`` exposed). Each call:

1. checks the in-process response cache (identical input -> no API call);
2. tries the primary provider (``config.LLM_PROVIDER``), which retries transient
   errors internally with backoff;
3. on any failure, falls over to the other provider (when
   ``config.LLM_FALLBACK_ENABLED``);
4. raises ``AllProvidersFailed`` only if every available provider failed.

A bounded semaphore caps how many provider calls run at once — background tasks
run in a threadpool, so a burst of uploads would otherwise hit the quota all at
once.
"""
from __future__ import annotations

import threading

from app import config
from app.core.logger import logger
from app.services.llm.base import AllProvidersFailed, LLMError
from app.services.llm.cache import LRUCache, key_for
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.prompts import contains_devanagari

_PROVIDERS = {
    "gemini": GeminiProvider(),
    "openai": OpenAIProvider(),
}

_sem = threading.BoundedSemaphore(max(1, config.LLM_MAX_CONCURRENCY))
_cache = LRUCache(config.LLM_CACHE_MAXSIZE)


def _ordered_providers(prefer: str | None = None) -> list:
    """Primary first, then the other one when failover is enabled.

    `prefer` (from a per-request hint, e.g. the UI's provider picker) overrides
    `config.LLM_PROVIDER` for that call only; "auto"/None/unknown falls back to
    the configured default."""
    primary = prefer if prefer in _PROVIDERS else config.LLM_PROVIDER
    if primary not in _PROVIDERS:
        primary = "gemini"
    order = [primary]
    if config.LLM_FALLBACK_ENABLED:
        order += [n for n in _PROVIDERS if n != primary]
    return [_PROVIDERS[n] for n in order]


def any_provider_available() -> bool:
    return any(p.available() for p in _ordered_providers())


def _enforce_sinhala_script(method: str, provider, result):
    """The transcriber sometimes renders spoken Sinhala in Devanagari (Hindi)
    script. When that slips past the hardened prompt, ask the same provider to
    rewrite it in Sinhala script — once, best effort."""
    if method not in ("transcribe_audio", "translate_text"):
        return result
    if not (isinstance(result, tuple) and len(result) == 2):
        return result
    transcript, translation = result
    if not contains_devanagari(transcript):
        return result
    try:
        fixed = provider.rescript_to_sinhala(transcript)
        if contains_devanagari(fixed):
            logger.warning("rescript still contains Devanagari: %r", fixed)
        return (fixed, translation)
    except LLMError as e:
        logger.warning("rescript_to_sinhala failed, keeping original: %s", e)
        return result


def _dispatch(method: str, cache_key: str | None, *args, prefer: str | None = None):
    if cache_key is not None:
        hit = _cache.get(cache_key)
        if hit is not None:
            logger.info("llm %s: cache hit", method)
            return hit

    attempts: list[str] = []
    tried_any = False
    for provider in _ordered_providers(prefer):
        if not provider.available():
            attempts.append(f"{provider.name}: no credentials")
            continue
        tried_any = True
        try:
            with _sem:
                result = getattr(provider, method)(*args)
            if attempts:
                logger.warning("llm %s: recovered on %s after %s",
                               method, provider.name, "; ".join(attempts))
            result = _enforce_sinhala_script(method, provider, result)
            if cache_key is not None:
                _cache.set(cache_key, result)
            return result
        except LLMError as e:
            logger.warning("llm %s: %s failed (%s)", method, provider.name, e)
            attempts.append(f"{provider.name}: {e}")
        except Exception as e:  # pragma: no cover - defensive
            logger.exception("llm %s: %s raised unexpectedly", method, provider.name)
            attempts.append(f"{provider.name}: {type(e).__name__}: {e}")

    if not tried_any:
        attempts.append("no LLM provider is configured (set GEMINI_API_KEY or OPENAI_API_KEY)")
    raise AllProvidersFailed(attempts)


def transcribe_audio(audio_bytes: bytes, prefer: str | None = None) -> tuple[str, str]:
    return _dispatch("transcribe_audio", key_for("transcribe", audio_bytes),
                     audio_bytes, prefer=prefer)


def translate_text(text: str, prefer: str | None = None) -> tuple[str, str]:
    return _dispatch("translate_text", key_for("translate", text), text, prefer=prefer)


def analyze_image(image_bytes: bytes, mime_type: str, caption: str = "",
                  prefer: str | None = None) -> dict:
    return _dispatch(
        "analyze_image",
        key_for("vision", image_bytes, mime_type, caption),
        image_bytes, mime_type, caption, prefer=prefer,
    )
