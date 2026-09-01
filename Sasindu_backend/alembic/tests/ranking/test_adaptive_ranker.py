import numpy as np

from app.ranking.adaptive_ranker import AdaptiveRanker
from app.ranking.features import CandidateFeatures
from app.ranking.weight_profiles import ARMS


def test_rank_returns_scored_candidates_and_chosen_arm_index():
    ranker = AdaptiveRanker(context_dim=3)
    features = [
        CandidateFeatures("p1", rating=0.8, availability=0.8, reliability=0.8, response_speed=0.8, eta_score=0.8),
        CandidateFeatures("p2", rating=0.2, availability=0.2, reliability=0.2, response_speed=0.2, eta_score=0.2),
    ]
    context = np.array([1.0, 0.0, 0.0])
    scored, arm_index = ranker.rank(context, features)

    assert [s.provider_id for s in scored] == ["p1", "p2"]
    assert 0 <= arm_index < len(ARMS)


def test_ranker_state_persists_across_calls_and_feedback_shifts_future_choices():
    ranker = AdaptiveRanker(context_dim=2, alpha=0.1)
    context = np.array([1.0, 1.0])

    for _ in range(60):
        ranker.record_feedback(context, arm_index=1, reward=1.0)
        ranker.record_feedback(context, arm_index=0, reward=0.0)

    chosen_arm = ranker.bandit.select_arm(context)
    assert chosen_arm == 1
