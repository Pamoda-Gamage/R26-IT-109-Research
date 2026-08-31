"""should_fallback_to_gemini is a pure function — exercise every reason row
without loading CLIP."""
import pytest

from app import config
from app.services.image_recognition_service import should_fallback_to_gemini

# A local result the policy should be happy with.
CLEAN = {
    "object_type": "vehicle",
    "object_type_confidence": 0.92,
    "object_type_top2_margin": 0.60,
    "subtype": "lorry_truck",
    "subtype_confidence": 0.80,
    "service_type": "mechanic",
    "service_type_confidence": 0.85,
}


@pytest.fixture(autouse=True)
def _fallback_enabled(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_GEMINI_FALLBACK", True)


def test_clean_result_does_not_fall_back():
    do, reasons = should_fallback_to_gemini(CLEAN)
    assert do is False and reasons == []


def test_disabled_flag_short_circuits(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_GEMINI_FALLBACK", False)
    do, reasons = should_fallback_to_gemini({**CLEAN, "object_type": "other"})
    assert do is False and reasons == []


@pytest.mark.parametrize(
    "patch, reason",
    [
        ({"object_type_confidence": 0.10}, "low_object_type_conf"),
        ({"object_type_top2_margin": 0.01}, "small_top2_margin"),
        ({"object_type": "other"}, "object_type_other"),
        ({"subtype": None, "subtype_confidence": 0.0}, "subtype_unknown"),
        ({"subtype_confidence": 0.10}, "subtype_unknown"),
        ({"service_type": None, "service_type_confidence": 0.1}, "low_service_type_conf"),
        ({"subtype": "refrigerator"}, "cross_head_disagreement"),
    ],
)
def test_each_reason_triggers(patch, reason):
    do, reasons = should_fallback_to_gemini({**CLEAN, **patch})
    assert do is True
    assert reason in reasons


def test_image_text_service_mismatch():
    result = {**CLEAN, "service_type_confidence": 0.50}
    do, reasons = should_fallback_to_gemini(result, text_service_type="plumber")
    assert do is True
    assert "image_text_service_mismatch" in reasons
