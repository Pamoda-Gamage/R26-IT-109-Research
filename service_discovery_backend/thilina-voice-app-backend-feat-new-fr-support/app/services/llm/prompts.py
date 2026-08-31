"""Prompt text + response parsing shared by every provider.

Keeping these here (rather than in a single provider) means Gemini and OpenAI
send byte-identical instructions, so their outputs stay comparable and a
failover doesn't change behaviour.
"""
from __future__ import annotations

from app.core.logger import logger
from app.services import image_taxonomy as tax

TRANSCRIBE_PROMPT = """Transcribe this audio exactly as spoken, then translate it to English.
The speaker is Sri Lankan; their language is Sinhala, Tamil, or English, often code-mixed
(Singlish).

Rules for transcript:
- Write Sinhala only in Sinhala (Sinhalese) script — Unicode range U+0D80 to U+0DFF. Do not
  romanize Sinhala.
- NEVER output Devanagari / Hindi script (U+0900 to U+097F) or any other Indic script. If the
  speech sounds like Hindi, it is Sinhala — render it in Sinhala script.
- Keep English words as English (don't translate them). Keep Tamil in Tamil script.
- Do not add punctuation, commentary, or explanations.

Rules for translation:
- Provide a natural English translation of the full utterance.
- Preserve named entities, numbers, and locations as accurately as possible.

Respond ONLY with a JSON object in this exact format, nothing else:
{"transcript": "...", "translation": "..."}"""

TRANSLATE_PROMPT = """Take this typed text, then translate it to English.
The text may mix Sinhala and English (Singlish/code-mixed writing), and Sinhala
may appear either in Sinhala script or romanized.

Rules for transcript:
- Rewrite the text with any Sinhala portions in Sinhala (Sinhalese) script — Unicode range
  U+0D80 to U+0DFF (convert romanized Sinhala to Sinhala script).
- NEVER output Devanagari / Hindi script (U+0900 to U+097F) or any other Indic script. If a
  portion looks like Hindi, it is Sinhala — render it in Sinhala script.
- Keep English words as English (don't translate them). Keep Tamil in Tamil script.
- Do not add punctuation, commentary, or explanations.
- If the text is already all English, return it unchanged.

Rules for translation:
- Provide a natural English translation of the full text.
- Preserve named entities, numbers, and locations as accurately as possible.
- Do not add commentary or explanations.

Respond ONLY with a JSON object in this exact format, nothing else:
{"transcript": "...", "translation": "..."}"""


RESCRIPT_PROMPT = """Rewrite the following text so that every Sinhala portion is written in
Sinhala (Sinhalese) script — Unicode range U+0D80 to U+0DFF.
The text may currently be in Devanagari / Hindi script or romanized; convert it to Sinhala
script with the SAME meaning and pronunciation.

- Do not translate, summarise, correct, or add anything.
- Keep English words in English. Keep any Tamil in Tamil script.
- Do not add punctuation or commentary.

Respond ONLY with a JSON object in this exact format, nothing else:
{"transcript": "..."}"""


def contains_devanagari(text: str) -> bool:
    """True if `text` has any Devanagari codepoint (U+0900–U+097F) — the script
    the transcriber wrongly falls back to for spoken Sinhala."""
    return any(0x0900 <= ord(ch) <= 0x097F for ch in (text or ""))

_VISION_PROMPT_V2_TEMPLATE = """You are triaging a photo submitted alongside a home/vehicle/appliance
service request. The local recogniser was not confident, so analyse the photo
carefully.

1. object_type — pick exactly one:
{object_types}
   Use "other" if none fit.

2. subtype — pick exactly one from the options for the object_type you chose
   (this is the routing-critical detail; e.g. a lorry vs a car both map to a
   "mechanic" but must NOT be treated the same):
{subtypes_block}
   Use "other" if none fit.

3. service_type — the single closest-matching category strictly from:
{service_types}
   Use "unknown" if nothing plausibly fits.

4. conditions — a JSON array (0 or more) of what looks wrong, strictly from:
{conditions}
   Use [] if nothing looks wrong.

5. description — one or two plain-English sentences a dispatcher can act on.
{caption_context}
Respond ONLY with a JSON object in this exact format, nothing else:
{{"object_type": "...", "subtype": "...", "service_type": "...",
  "conditions": ["..."], "description": "..."}}"""


def _subtypes_block() -> str:
    lines = []
    for ot in tax.OBJECT_TYPES:
        opts = ", ".join(tax.SUBTYPE_LABELS.get(ot, []))
        if opts:
            lines.append(f"   - {ot}: {opts}")
    return "\n".join(lines)


def build_vision_prompt(caption: str = "") -> str:
    caption_context = (
        f'\nThe user captioned this photo: "{caption}"\n' if caption.strip() else ""
    )
    return _VISION_PROMPT_V2_TEMPLATE.format(
        object_types=", ".join(tax.OBJECT_TYPES),
        subtypes_block=_subtypes_block(),
        service_types=", ".join(tax.KNOWN_SERVICE_TYPES),
        conditions=", ".join(tax.CONDITION_TAGS),
        caption_context=caption_context,
    )


def _validate_choice(value, allowed, field: str, fallback):
    v = (value or "").strip() if isinstance(value, str) else value
    if v in allowed:
        return v
    if v and v not in ("unknown", "other", "none"):
        logger.warning("LLM returned out-of-vocab %s: %r", field, v)
    return fallback


def finalize_vision_result(parsed: dict, raw: str) -> dict:
    """Turn a provider's parsed JSON (or {} on parse failure, with `raw` text)
    into the canonical vision dict — identical regardless of which provider
    produced it."""
    description = parsed.get("description", "").strip() if parsed else raw
    object_type = _validate_choice(parsed.get("object_type"), set(tax.OBJECT_TYPES),
                                   "object_type", "other")
    subtype = _validate_choice(parsed.get("subtype"), set(tax.ALL_SUBTYPES),
                               "subtype", None)
    if subtype == "other":
        subtype = None
    service_type = _validate_choice(parsed.get("service_type"),
                                    set(tax.KNOWN_SERVICE_TYPES), "service_type", None)

    raw_conditions = parsed.get("conditions") or []
    if isinstance(raw_conditions, str):
        raw_conditions = [raw_conditions]
    conditions = [c for c in raw_conditions if c in set(tax.CONDITION_TAGS)] or ["no_visible_problem"]

    logger.info("llm vision: object_type=%s subtype=%s service_type=%s",
                object_type, subtype, service_type)

    return {
        "object_type": object_type,
        # LLMs give no calibrated probabilities; use fixed moderate-high
        # confidences so downstream gates treat a fallback result as usable.
        "object_type_confidence": 0.9 if object_type != "other" else 0.3,
        "object_type_top2_margin": 0.5,
        "subtype": subtype,
        "subtype_confidence": 0.9 if subtype else 0.0,
        "service_type": service_type,
        "service_type_confidence": 0.9 if service_type else 0.0,
        "conditions": conditions,
        "condition_scores": {},
        "description": description,
        "suggested_service_type": service_type,
        "recognition_source": "gemini_fallback",
    }
