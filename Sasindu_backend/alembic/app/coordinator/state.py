import operator
from typing import Annotated, Any, TypedDict

from app.availability.availability_agent import AvailabilityInfo
from app.context.context_agent import ContextOutput
from app.ranking.static_ranker import ScoredCandidate
from app.routing.dijkstra import PathResult


class TraceEvent(TypedDict):
    node: str
    started_at: str
    ended_at: str
    detail: dict[str, Any]


class PipelineState(TypedDict):
    request_id: str
    raw_text: str
    timestamp: str
    region: str
    context: ContextOutput | None
    search_results: list[str]
    distances: dict[str, PathResult]
    availability: dict[str, AvailabilityInfo]
    ranked: list[ScoredCandidate]
    chosen_arm_index: int | None
    context_vector: list[float]
    # Every node returns {"trace": [one_event]} -- without this reducer, LangGraph's
    # default "last write wins" merge would make each node's update *replace* the
    # trace instead of appending to it, and the final trace would only ever show the
    # last node that ran.
    trace: Annotated[list[TraceEvent], operator.add]


def new_pipeline_state(request_id: str, raw_text: str, timestamp: str, region: str) -> PipelineState:
    return PipelineState(
        request_id=request_id,
        raw_text=raw_text,
        timestamp=timestamp,
        region=region,
        context=None,
        search_results=[],
        distances={},
        availability={},
        ranked=[],
        chosen_arm_index=None,
        context_vector=[],
        trace=[],
    )
