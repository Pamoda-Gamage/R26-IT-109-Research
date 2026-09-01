import json

from app.context.toon_serializer import to_toon


def test_to_toon_produces_header_and_pipe_delimited_rows():
    rows = [
        {"field": "time_slot", "value": "evening_peak"},
        {"field": "raw_text", "value": "need a plumber right now, pipe burst"},
    ]
    output = to_toon(rows)
    lines = output.strip().split("\n")
    assert lines[0] == "field|value"
    assert lines[1] == "time_slot|evening_peak"
    assert lines[2] == "raw_text|need a plumber right now, pipe burst"


def test_to_toon_is_shorter_than_equivalent_json():
    rows = [{"field": f"f{i}", "value": f"v{i}"} for i in range(10)]
    toon_len = len(to_toon(rows))
    json_len = len(json.dumps(rows))
    assert toon_len < json_len
