from dataclasses import dataclass


@dataclass
class CandidateInput:
    provider_id: str
    rating: float
    availability_probability: float
    reliability_alpha: float
    reliability_beta: float
    base_response_speed: float
    eta_minutes: float


@dataclass
class CandidateFeatures:
    provider_id: str
    rating: float
    availability: float
    reliability: float
    response_speed: float
    eta_score: float


def _invert_normalize(value: float, min_v: float, max_v: float) -> float:
    """Lower raw value -> higher normalized score (used for minutes-based features)."""
    if max_v == min_v:
        return 1.0
    clamped = max(min_v, min(max_v, value))
    return 1.0 - (clamped - min_v) / (max_v - min_v)


def build_features(inputs: list[CandidateInput]) -> list[CandidateFeatures]:
    if not inputs:
        return []

    response_speeds = [c.base_response_speed for c in inputs]
    etas = [c.eta_minutes for c in inputs]
    speed_min, speed_max = min(response_speeds), max(response_speeds)
    eta_min, eta_max = min(etas), max(etas)

    features = []
    for c in inputs:
        reliability = c.reliability_alpha / (c.reliability_alpha + c.reliability_beta)
        features.append(
            CandidateFeatures(
                provider_id=c.provider_id,
                rating=c.rating / 5.0,
                availability=c.availability_probability,
                reliability=reliability,
                response_speed=_invert_normalize(c.base_response_speed, speed_min, speed_max),
                eta_score=_invert_normalize(c.eta_minutes, eta_min, eta_max),
            )
        )
    return features
