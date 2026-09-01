from functools import partial

from langgraph.graph import END, StateGraph

from app.coordinator.nodes import availability_node, context_node, distance_node, ranking_node, search_node
from app.coordinator.routing_condition import route_by_urgency
from app.coordinator.state import PipelineState


def build_graph(
    context_agent,
    search_agent,
    distance_agent,
    availability_agent,
    adaptive_ranker,
    provider_nodes: dict[str, int],
    source_node_resolver,
    session_factory,
    provider_lookup_factory,
):
    graph = StateGraph(PipelineState)

    # These three need a value computed fresh from `state` (or from a factory) on every
    # call -- functools.partial can't do that (its bound args are fixed at definition
    # time), and a plain `lambda state: distance_node(...)` returns an *unawaited*
    # coroutine, since the lambda itself isn't a coroutine function and LangGraph never
    # awaits its return value. Real `async def` closures are both awaitable and able to
    # recompute per-call arguments.
    async def _distance(state: PipelineState) -> dict:
        return await distance_node(
            state,
            distance_agent=distance_agent,
            provider_nodes=provider_nodes,
            source_node=source_node_resolver(state),
        )

    async def _availability(state: PipelineState) -> dict:
        return await availability_node(state, availability_agent=availability_agent, session=session_factory())

    async def _ranking(state: PipelineState) -> dict:
        return await ranking_node(state, adaptive_ranker=adaptive_ranker, provider_lookup=provider_lookup_factory())

    graph.add_node("context", partial(context_node, context_agent=context_agent))
    graph.add_node("search", partial(search_node, search_agent=search_agent))
    graph.add_node("distance", _distance)
    graph.add_node("availability", _availability)
    graph.add_node("ranking", _ranking)

    graph.set_entry_point("context")
    graph.add_conditional_edges(
        "context",
        route_by_urgency,
        {"emergency_path": "search", "normal_path": "search"},
    )
    graph.add_edge("search", "distance")
    graph.add_edge("distance", "availability")
    graph.add_edge("availability", "ranking")
    graph.add_edge("ranking", END)

    return graph.compile()
