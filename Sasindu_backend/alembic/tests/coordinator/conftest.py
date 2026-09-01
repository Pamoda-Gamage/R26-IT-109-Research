from dataclasses import dataclass

from app.context.context_agent import ContextOutput
from app.ranking.static_ranker import ScoredCandidate
from app.routing.dijkstra import PathResult


@dataclass
class FakeProvider:
    rating: float
    reliability_alpha: float
    reliability_beta: float
    base_response_speed: float


class FakeContextAgent:
    def __init__(self, urgency: str = "normal", time_slot: str = "midday"):
        self._urgency = urgency
        self._time_slot = time_slot

    async def infer(self, raw_text, timestamp, region):
        return ContextOutput(time_slot=self._time_slot, region=region, urgency=self._urgency, constraints=[])


class FakeSearchAgent:
    def __init__(self, normal_results=None, emergency_results=None):
        self._normal_results = normal_results if normal_results is not None else ["p1", "p2", "p3"]
        self._emergency_results = emergency_results if emergency_results is not None else ["p1"]

    def retrieve(self, query, service_type, region, is_emergency, mode="hybrid"):
        return self._emergency_results if is_emergency else self._normal_results


class FakeDistanceAgent:
    def score_candidates(self, providers, source_node, time_slot, algorithm="dijkstra"):
        return {
            p.provider_id: PathResult(nodes=[source_node, p.node_id], distance_m=1000.0, eta_minutes=5.0 + i)
            for i, p in enumerate(providers)
        }


class FakeAvailabilityAgent:
    async def filter_and_score(self, session, provider_ids):
        from app.availability.availability_agent import AvailabilityInfo

        return {pid: AvailabilityInfo(status="online", acceptance_probability=0.9) for pid in provider_ids}


class FakeAdaptiveRanker:
    def rank(self, context, features):
        scored = [ScoredCandidate(provider_id=f.provider_id, score=1.0) for f in features]
        return scored, 0
