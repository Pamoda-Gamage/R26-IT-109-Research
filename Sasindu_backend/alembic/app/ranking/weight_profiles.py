from app.ranking.static_ranker import PP1_BASELINE_WEIGHTS, WeightProfile

ARMS: list[WeightProfile] = [
    PP1_BASELINE_WEIGHTS,  # "balanced" -- the PP1 control
    WeightProfile(
        rating=0.10, availability=0.15, reliability=0.15, response_speed=0.10, eta_score=0.50
    ),  # "eta_heavy" -- emergencies
    WeightProfile(
        rating=0.45, availability=0.15, reliability=0.20, response_speed=0.10, eta_score=0.10
    ),  # "rating_heavy" -- non-urgent, quality-seeking
    WeightProfile(
        rating=0.15, availability=0.15, reliability=0.50, response_speed=0.10, eta_score=0.10
    ),  # "reliability_heavy" -- repeat/high-stakes jobs
]

ARM_NAMES: list[str] = ["balanced_pp1_baseline", "eta_heavy", "rating_heavy", "reliability_heavy"]
