from app.context.schema import ContextResult, parse_llm_output


def test_parses_valid_json():
    raw = '{"urgency": "emergency", "constraints": ["needs same-day service"], "confidence": 0.9}'
    result = parse_llm_output(raw)
    assert isinstance(result, ContextResult)
    assert result.urgency == "emergency"
    assert result.constraints == ["needs same-day service"]


def test_returns_none_on_malformed_json():
    assert parse_llm_output("not json at all {{{") is None


def test_returns_none_on_missing_required_field():
    assert parse_llm_output('{"urgency": "emergency"}') is None


def test_returns_none_on_invalid_enum_value():
    raw = '{"urgency": "catastrophic", "constraints": [], "confidence": 0.5}'
    assert parse_llm_output(raw) is None
