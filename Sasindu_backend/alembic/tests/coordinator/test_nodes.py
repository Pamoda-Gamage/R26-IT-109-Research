from datetime import UTC, datetime

from app.coordinator.nodes import availability_node, context_node, distance_node, ranking_node, search_node
from app.coordinator.state import new_pipeline_state
from tests.coordinator.conftest import (
    FakeAdaptiveRanker,
    FakeAvailabilityAgent,
    FakeContextAgent,
    FakeDistanceAgent,
    FakeProvider,
    FakeSearchAgent,
)


async def test_context_node_updates_state_and_appends_trace():
    state = new_pipeline_state("r1", "need a plumber", datetime.now(UTC).isoformat(), "colombo-01")
    update = await context_node(state, context_agent=FakeContextAgent())
    assert update["context"].urgency == "normal"
    assert len(update["trace"]) == 1
    assert update["trace"][0]["node"] == "context_agent"


async def test_search_node_uses_context_urgency_for_candidate_count():
    state = new_pipeline_state("r1", "need a plumber", datetime.now(UTC).isoformat(), "colombo-01")
    state["context"] = (await context_node(state, context_agent=FakeContextAgent(urgency="normal")))["context"]
    update = await search_node(state, search_agent=FakeSearchAgent())
    assert update["search_results"] == ["p1", "p2", "p3"]
    assert update["trace"][0]["detail"]["is_emergency"] is False


async def test_distance_node_scores_each_search_result():
    state = new_pipeline_state("r1", "need a plumber", datetime.now(UTC).isoformat(), "colombo-01")
    state["context"] = (await context_node(state, context_agent=FakeContextAgent()))["context"]
    state["search_results"] = ["p1", "p2"]
    provider_nodes = {"p1": 1, "p2": 2}
    update = await distance_node(
        state, distance_agent=FakeDistanceAgent(), provider_nodes=provider_nodes, source_node=0
    )
    assert set(update["distances"].keys()) == {"p1", "p2"}


async def test_availability_node_returns_info_for_every_distance_candidate():
    state = new_pipeline_state("r1", "need a plumber", datetime.now(UTC).isoformat(), "colombo-01")
    state["distances"] = {"p1": None, "p2": None}
    update = await availability_node(state, availability_agent=FakeAvailabilityAgent(), session=None)
    assert set(update["availability"].keys()) == {"p1", "p2"}


async def test_ranking_node_builds_features_and_returns_chosen_arm():
    state = new_pipeline_state("r1", "need a plumber", datetime.now(UTC).isoformat(), "colombo-01")
    state["context"] = (await context_node(state, context_agent=FakeContextAgent()))["context"]
    state["search_results"] = ["p1", "p2"]
    provider_nodes = {"p1": 1, "p2": 2}
    state["distances"] = (
        await distance_node(state, distance_agent=FakeDistanceAgent(), provider_nodes=provider_nodes, source_node=0)
    )["distances"]
    state["availability"] = (
        await availability_node(state, availability_agent=FakeAvailabilityAgent(), session=None)
    )["availability"]

    provider_lookup = {
        "p1": FakeProvider(rating=4.5, reliability_alpha=8.0, reliability_beta=2.0, base_response_speed=10.0),
        "p2": FakeProvider(rating=3.0, reliability_alpha=2.0, reliability_beta=8.0, base_response_speed=40.0),
    }
    update = await ranking_node(state, adaptive_ranker=FakeAdaptiveRanker(), provider_lookup=provider_lookup)
    assert {c.provider_id for c in update["ranked"]} == {"p1", "p2"}
    assert update["chosen_arm_index"] == 0
    assert update["trace"][0]["detail"]["candidates"] == 2
