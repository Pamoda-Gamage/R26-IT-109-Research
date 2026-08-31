"""Shared tenacity retry policy for provider API calls.

Only ``LLMTransient`` is retried (429 / 5xx / timeout / connection). A
``LLMPermanent`` (bad key, unknown model) escapes on the first try so the
dispatcher can fail over without waiting.
"""
from __future__ import annotations

import logging

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
)

from app.core.logger import logger
from app.services.llm.base import LLMTransient

with_retry = retry(
    retry=retry_if_exception_type(LLMTransient),
    wait=wait_exponential_jitter(initial=1, max=20),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
