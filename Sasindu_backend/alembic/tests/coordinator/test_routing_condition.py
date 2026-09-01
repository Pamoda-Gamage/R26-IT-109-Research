from app.context.context_agent import ContextOutput
from app.coordinator.routing_condition import route_by_urgency
from app.coordinator.state import new_pipeline_state


def test_routes_to_emergency_path_when_urgent():
    state = new_pipeline_state("r1", "text", "2026-01-01T00:00:00Z", "colombo-01")
    state["context"] = ContextOutput(time_slot="night", region="colombo-01", urgency="emergency", constraints=[])
    assert route_by_urgency(state) == "emergency_path"


def test_routes_to_normal_path_otherwise():
    state = new_pipeline_state("r1", "text", "2026-01-01T00:00:00Z", "colombo-01")
    state["context"] = ContextOutput(time_slot="midday", region="colombo-01", urgency="normal", constraints=[])
    assert route_by_urgency(state) == "normal_path"
