from app.coordinator.state import TraceEvent, new_pipeline_state


def test_new_pipeline_state_has_all_required_keys_and_empty_trace():
    state = new_pipeline_state(
        request_id="r1", raw_text="need a plumber", timestamp="2026-01-01T20:00:00Z", region="colombo-01"
    )
    assert state["request_id"] == "r1"
    assert state["trace"] == []
    assert state["context"] is None
    assert state["ranked"] == []
    assert state["chosen_arm_index"] is None


def test_trace_event_is_a_plain_dict_shape():
    event: TraceEvent = {"node": "context_agent", "started_at": "t0", "ended_at": "t1", "detail": {"urgency": "normal"}}
    assert event["node"] == "context_agent"
