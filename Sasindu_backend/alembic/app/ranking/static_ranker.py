from dataclasses import dataclass

from app.ranking.features import CandidateFeatures


@dataclass(frozen=True)
class WeightProfile:
    rating: float
    availability: float
    reliability: float
    response_speed: float
    eta_score: float


@dataclass
class ScoredCandidate:
    provider_id: str
    score: float


# Verbatim reproduction of PP1's hardcoded weights (srs.md §1.2), kept as the
# named experimental control for the adaptive system built in Phase 6.
PP1_BASELINE_WEIGHTS = WeightProfile(rating=0.3, availability=0.2, reliability=0.2, response_speed=0.1, eta_score=0.2)


class StaticRanker:
    def rank(
        self, features: list[CandidateFeatures], weights: WeightProfile = PP1_BASELINE_WEIGHTS
    ) -> list[ScoredCandidate]:
        scored = [
            ScoredCandidate(
                provider_id=f.provider_id,
                score=(
                    f.rating * weights.rating
                    + f.availability * weights.availability
                    + f.reliability * weights.reliability
                    + f.response_speed * weights.response_speed
                    + f.eta_score * weights.eta_score
                ),
            )
            for f in features
        ]
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored
