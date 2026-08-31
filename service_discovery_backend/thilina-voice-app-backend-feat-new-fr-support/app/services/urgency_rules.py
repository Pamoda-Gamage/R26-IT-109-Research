"""Deterministic urgency resolution from a reply to the "how urgent is this?"
clarifying question.

The local urgency head is miscalibrated and over-predicts "high" on short
utterances (see app/training/diagnose_urgency.py), so a reply like "can wait a
moment" comes back as "high". When we *know* the user is answering the urgency
question, their words are a better signal than the model — this module turns
those words into a label.

Pure string matching, no model/DB imports, so it's cheap to unit-test (mirrors
image_taxonomy.py). Styled after `_EMERGENCY_KEYWORDS` in predict_service.py.
"""
from __future__ import annotations

# "I need it now" — escalate to high. Checked with a negation guard (see
# `_mentions`) so "not urgent" / "no hurry" do NOT count as escalation.
_URGENCY_ANSWER_NOW = (
    # English
    "right away", "right now", "straight away", "immediately", "asap",
    "as soon as possible", "urgent", "urgently", "emergency", "come now",
    "need it now", "need someone now", "hurry", "quickly",
    # Sinhala
    "දැන්ම", "දැන්මම", "දැන්ම එන්න", "ඉක්මනට", "ඉක්මනින්", "හදිසියි",
    "හදිසියක්", "ඉක්මන්",
)

# "No hurry at all" — drop to low.
_URGENCY_ANSWER_WAIT_STRONG = (
    # English
    "no rush", "no hurry", "not urgent", "not in a hurry", "whenever",
    "any time", "anytime", "next week", "next month", "some other day",
    "another day", "in a few days", "later this week", "no problem to wait",
    "happy to wait", "take your time",
    # Sinhala
    "හදිසි නෑ", "හදිසි නැහැ", "ඉක්මන් නෑ", "ඉක්මන් නැහැ", "කවදා හරි",
    "ලබන සතියේ", "පස්සේ දවසක", "කලබල නෑ",
)

# "It can wait a bit" — medium.
_URGENCY_ANSWER_WAIT_MILD = (
    # English
    "can wait", "could wait", "it can wait", "wait a bit", "wait a moment",
    "wait a while", "a bit later", "later today", "sometime today",
    "in a day or two", "day or two", "tomorrow", "soon", "when you can",
    "when possible", "not right now",
    # Sinhala
    "ඉන්න පුළුවන්", "පොඩ්ඩක් ඉන්න", "ටිකක් ඉන්න", "පස්සේ", "හෙට",
    "පොඩ්ඩක් පරක්කු",
)

_NEGATED_WAIT = (
    "can't wait", "cant wait", "can not wait", "cannot wait",
    "won't wait", "wont wait", "will not wait",
)

# Trailing tokens that flip the meaning of a phrase that follows them.
_NEGATORS = ("not", "n't", "no", "never", "isn't", "aren't", "wasn't", "don't")


def _mentions(text: str, phrases: tuple[str, ...]) -> bool:
    """True if any phrase occurs in `text` without a negator immediately before
    it — so "urgent" matches "it's urgent" but not "not urgent" / "no hurry"."""
    for phrase in phrases:
        start = 0
        while (i := text.find(phrase, start)) != -1:
            prefix = text[max(0, i - 10):i].rstrip(" ,-")
            if not any(prefix.endswith(neg) for neg in _NEGATORS):
                return True
            start = i + len(phrase)
    return False


def resolve_urgency_from_clarifying_answer(answer_text: str | None) -> str | None:
    """Return "high" | "medium" | "low" for a reply to the urgency question, or
    None when the reply is ambiguous (caller keeps the model's prediction)."""
    text = (answer_text or "").lower()
    if not text:
        return None

    if any(p in text for p in _NEGATED_WAIT) or _mentions(text, _URGENCY_ANSWER_NOW):
        return "high"
    if any(p in text for p in _URGENCY_ANSWER_WAIT_STRONG):
        return "low"
    if any(p in text for p in _URGENCY_ANSWER_WAIT_MILD):
        return "medium"
    return None
