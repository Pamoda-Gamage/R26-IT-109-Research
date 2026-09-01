from datetime import UTC, datetime

import numpy as np

from app.coordinator.state import PipelineState, TraceEvent
from app.ranking.features import CandidateInput, build_features
from app.ranking.weight_profiles import ARM_NAMES
from app.routing.distance_agent import ProviderLocation

TIME_SLOT_ORDER = ["early_morning", "morning_peak", "midday", "evening_peak", "night"]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _trace(node: str, started_at: str, detail: dict) -> TraceEvent:
    return TraceEvent(node=node, started_at=started_at, ended_at=_now(), detail=detail)


async def context_node(state: PipelineState, context_agent) -> dict:
    started = _now()
    context = await context_agent.infer(state["raw_text"], datetime.fromisoformat(state["timestamp"]), state["region"])
    return {
        "context": context,
        "trace": [
            _trace(
                "context_agent",
                started,
                {"urgency": context.urgency, "time_slot": context.time_slot, "constraints": context.constraints},
            )
        ],
    }


async def search_node(state: PipelineState, search_agent) -> dict:
    started = _now()
    context = state["context"]
    is_emergency = context.urgency == "emergency"

    service_type = None

    raw_text = state["raw_text"]
    if "[FILTER_SERVICE_TYPE:" in raw_text:
        match = raw_text.split("[FILTER_SERVICE_TYPE:")[1].split("]")[0]
        if match and match != "any":
            service_type = match

    if not service_type and context.constraints:
        for constraint in context.constraints:
            constraint_lower = constraint.lower()
            if "plumber" in constraint_lower:
                service_type = "plumbing"
            elif "carpenter" in constraint_lower:
                service_type = "carpentry"
            elif "electrician" in constraint_lower or "electric" in constraint_lower:
                service_type = "electrical"
            elif "paint" in constraint_lower:
                service_type = "painting"
            elif "hvac" in constraint_lower or "air" in constraint_lower:
                service_type = "hvac"
            elif "roof" in constraint_lower:
                service_type = "roofing"
            if service_type:
                break

    results = search_agent.retrieve(
        query=state["raw_text"], service_type=service_type, region=context.region, is_emergency=is_emergency
    )
    return {
        "search_results": results,
        "trace": [
            _trace(
                "search_agent",
                started,
                {"count": len(results), "is_emergency": is_emergency, "filtered_by": service_type or "none"},
            )
        ],
    }


async def distance_node(state: PipelineState, distance_agent, provider_nodes: dict[str, int], source_node: int) -> dict:
    started = _now()
    locations = [
        ProviderLocation(provider_id=pid, lat=0.0, lon=0.0, node_id=provider_nodes[pid])
        for pid in state["search_results"]
        if pid in provider_nodes
    ]
    results = distance_agent.score_candidates(locations, source_node=source_node, time_slot=state["context"].time_slot)
    return {"distances": results, "trace": [_trace("distance_agent", started, {"scored": len(results)})]}


async def availability_node(state: PipelineState, availability_agent, session) -> dict:
    started = _now()
    results = await availability_agent.filter_and_score(session, list(state["distances"].keys()))
    return {"availability": results, "trace": [_trace("availability_agent", started, {"available": len(results)})]}


async def ranking_node(state: PipelineState, adaptive_ranker, provider_lookup: dict) -> dict:
    started = _now()
    context = state["context"]
    inputs = []
    for provider_id, availability in state["availability"].items():
        path = state["distances"][provider_id]
        provider = provider_lookup[provider_id]
        inputs.append(
            CandidateInput(
                provider_id=provider_id,
                rating=provider.rating,
                availability_probability=availability.acceptance_probability,
                reliability_alpha=provider.reliability_alpha,
                reliability_beta=provider.reliability_beta,
                base_response_speed=provider.base_response_speed,
                eta_minutes=path.eta_minutes,
            )
        )
    features = build_features(inputs)

    time_slot_onehot = [1.0 if context.time_slot == slot else 0.0 for slot in TIME_SLOT_ORDER]
    context_vector = np.array([1.0 if context.urgency == "emergency" else 0.0, *time_slot_onehot])

    ranked, arm_index = adaptive_ranker.rank(context_vector, features)
    return {
        "ranked": ranked,
        "chosen_arm_index": arm_index,
        "context_vector": context_vector.tolist(),
        "trace": [_trace("ranking_agent", started, {"chosen_arm": ARM_NAMES[arm_index], "candidates": len(ranked)})],
    }
