"""Consistency checks for the image-recognition taxonomy — no model load."""
from app.services import image_taxonomy as tax


def test_validate_passes():
    tax.validate()


def test_every_subtype_maps_to_known_service_or_none():
    known = set(tax.KNOWN_SERVICE_TYPES)
    for s in tax.ALL_SUBTYPES:
        v = tax.service_type_for_subtype(s)
        assert v is None or v in known, (s, v)


def test_subtypes_for_includes_other_escape_hatch():
    for ot in tax.OBJECT_TYPES:
        assert "other" in tax.subtypes_for(ot)


def test_prompt_bank_covers_every_label():
    needed = (
        set(tax.OBJECT_TYPES)
        | set(tax.ALL_SUBTYPES)
        | set(tax.CONDITION_TAGS)
        | set(tax.KNOWN_SERVICE_TYPES)
    )
    assert needed <= set(tax.PROMPT_BANK)
    assert all(tax.PROMPT_BANK[k] for k in needed)


def test_object_type_service_masks_are_known_labels():
    known = set(tax.KNOWN_SERVICE_TYPES)
    for ot, allowed in tax.OBJECT_TYPE_TO_SERVICE_TYPES.items():
        assert allowed <= known, (ot, allowed - known)
