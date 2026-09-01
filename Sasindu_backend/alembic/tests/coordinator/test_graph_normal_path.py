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


async def test_normal_path_visits_all_five_nodes_in_order():
    compiled_graph = _build_test_graph(urgency="normal", normal_results=["p1", "p2", "p3"])
    state = new_pipeline_state("r1", "need a plumber", "2026-01-01T12:00:00Z", "colombo-01")

    final_state = await compiled_graph.ainvoke(state)

    node_sequence = [event["node"] for event in final_state["trace"]]
    assert node_sequence == ["context_agent", "search_agent", "distance_agent", "availability_agent", "ranking_agent"]
    assert final_state["context"].urgency == "normal"
    assert len(final_state["ranked"]) == 3
