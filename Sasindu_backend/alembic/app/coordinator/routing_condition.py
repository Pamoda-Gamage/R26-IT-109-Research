from typing import Literal

from app.coordinator.state import PipelineState


def route_by_urgency(state: PipelineState) -> Literal["emergency_path", "normal_path"]:
    context = state["context"]
    assert context is not None, "route_by_urgency called before context_node ran"
    return "emergency_path" if context.urgency == "emergency" else "normal_path"
