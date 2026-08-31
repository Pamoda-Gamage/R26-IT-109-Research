"""Back-compat shim.

The transcription / translation / vision logic moved to ``app.services.llm``,
which adds automatic OpenAI failover, retry/backoff, a concurrency cap and a
response cache. Import from ``app.services.llm`` directly in new code; this
module stays only so existing imports keep working.
"""
from app.services.llm import (  # noqa: F401
    AllProvidersFailed,
    LLMError,
    analyze_image,
    analyze_image_v2,
    any_provider_available,
    transcribe_audio,
    translate_text,
)
from app.services.llm.prompts import (  # noqa: F401
    TRANSCRIBE_PROMPT,
    TRANSLATE_PROMPT,
    build_vision_prompt,
)

# Old name for "is the LLM path usable at all" — now true if *any* provider
# (Gemini or OpenAI) has credentials.
gemini_available = any_provider_available
