from app.coordinator.graph import build_graph
from app.coordinator.state import new_pipeline_state
from tests.coordinator.conftest import (
    FakeAdaptiveRanker,
    FakeAvailabilityAgent,
    FakeContextAgent,
    FakeDistanceAgent,
    FakeProvider,
    FakeSearchAgent,
)


def _build_test_graph(urgency: str, normal_results=None, emergency_results=None):
    provider_nodes = {"p1": 1, "p2": 2, "p3": 3}
    provider_lookup = {
        pid: FakeProvider(rating=4.0, reliability_alpha=5.0, reliability_beta=5.0, base_response_speed=15.0)
        for pid in provider_nodes
    }
    return build_graph(
        context_agent=FakeContextAgent(urgency=urgency),
        search_agent=FakeSearchAgent(normal_results=normal_results, emergency_results=emergency_results),
        distance_agent=FakeDistanceAgent(),
        availability_agent=FakeAvailabilityAgent(),
        adaptive_ranker=FakeAdaptiveRanker(),
        provider_nodes=provider_nodes,
        source_node_resolver=lambda state: 0,
        session_factory=lambda: None,
        provider_lookup_factory=lambda: provider_lookup,
    )


async def test_emergency_path_uses_reduced_candidate_set():
    compiled_graph = _build_test_graph(
        urgency="emergency", normal_results=["p1", "p2", "p3"], emergency_results=["p1"]
    )
    state = new_pipeline_state("r1", "pipe burst, need help now", "2026-01-01T21:00:00Z", "colombo-01")

    final_state = await compiled_graph.ainvoke(state)

    search_trace = next(event for event in final_state["trace"] if event["node"] == "search_agent")
    assert search_trace["detail"]["is_emergency"] is True
    assert search_trace["detail"]["count"] == 1
    assert final_state["context"].urgency == "emergency"
    assert len(final_state["ranked"]) == 1


async def test_emergency_and_normal_paths_visit_the_same_five_nodes():
    """The conditional edge changes candidate volume (via search_agent's is_emergency
    branch), not the node sequence -- both paths converge through the same graph."""
    emergency_graph = _build_test_graph(urgency="emergency", emergency_results=["p1"])
    normal_graph = _build_test_graph(urgency="normal", normal_results=["p1", "p2"])

    emergency_state = await emergency_graph.ainvoke(
        new_pipeline_state("r1", "urgent!", "2026-01-01T21:00:00Z", "colombo-01")
    )
    normal_state = await normal_graph.ainvoke(new_pipeline_state("r2", "routine", "2026-01-01T12:00:00Z", "colombo-01"))

    expected_nodes = ["context_agent", "search_agent", "distance_agent", "availability_agent", "ranking_agent"]
    assert [e["node"] for e in emergency_state["trace"]] == expected_nodes
    assert [e["node"] for e in normal_state["trace"]] == expected_nodes
