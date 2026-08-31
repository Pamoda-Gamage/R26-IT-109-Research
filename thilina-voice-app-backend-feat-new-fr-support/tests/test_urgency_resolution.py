"""Pure tests for the urgency-from-clarifying-answer resolver — no model load."""
from app.services.urgency_rules import resolve_urgency_from_clarifying_answer as r


def test_mild_wait_is_medium():
    assert r("it can wait a moment") == "medium"
    assert r("sometime tomorrow is fine") == "medium"
    assert r("පොඩ්ඩක් ඉන්න පුළුවන්") == "medium"


def test_strong_wait_is_low():
    assert r("no rush, sometime next week is fine") == "low"
    assert r("whenever you can, no hurry") == "low"
    assert r("හදිසි නෑ") == "low"


def test_now_is_high():
    assert r("I need someone right away") == "high"
    assert r("this is urgent") == "high"
    assert r("දැන්ම එන්න") == "high"


def test_cant_wait_is_high_not_lowered():
    assert r("this can't wait") == "high"
    assert r("no, it cannot wait") == "high"


def test_ambiguous_or_empty_is_none():
    assert r("my phone screen is cracked") is None
    assert r("") is None
    assert r(None) is None


def test_now_beats_wait_when_both_present():
    assert r("it can wait but honestly I need it right away") == "high"
