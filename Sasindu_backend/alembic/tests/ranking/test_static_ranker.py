from app.ranking.features import CandidateFeatures
from app.ranking.static_ranker import PP1_BASELINE_WEIGHTS, StaticRanker, WeightProfile


def test_pp1_baseline_weights_match_original_formula():
    # srs.md §1.2: "Scoring weights were fixed constants (0.3, 0.2, 0.2, 0.1, 0.2)"
    assert PP1_BASELINE_WEIGHTS.rating == 0.3
    assert PP1_BASELINE_WEIGHTS.availability == 0.2
    assert PP1_BASELINE_WEIGHTS.reliability == 0.2
    assert PP1_BASELINE_WEIGHTS.response_speed == 0.1
    assert PP1_BASELINE_WEIGHTS.eta_score == 0.2
    assert abs(sum(PP1_BASELINE_WEIGHTS.__dict__.values()) - 1.0) < 1e-9


def test_rank_is_deterministic_and_sorted_descending():
    features = [
        CandidateFeatures("p1", rating=0.9, availability=0.9, reliability=0.9, response_speed=0.9, eta_score=0.9),
        CandidateFeatures("p2", rating=0.1, availability=0.1, reliability=0.1, response_speed=0.1, eta_score=0.1),
    ]
    ranker = StaticRanker()
    result_a = ranker.rank(features)
    result_b = ranker.rank(features)
    assert [r.provider_id for r in result_a] == ["p1", "p2"]
    assert result_a == result_b


def test_custom_weight_profile_changes_ranking():
    features = [
        CandidateFeatures(
            "fast_low_rated", rating=0.2, availability=0.5, reliability=0.5, response_speed=0.5, eta_score=0.95
        ),
        CandidateFeatures(
            "slow_high_rated", rating=0.95, availability=0.5, reliability=0.5, response_speed=0.5, eta_score=0.2
        ),
    ]
    ranker = StaticRanker()
    eta_heavy = WeightProfile(rating=0.05, availability=0.05, reliability=0.05, response_speed=0.05, eta_score=0.8)
    result = ranker.rank(features, weights=eta_heavy)
    assert result[0].provider_id == "fast_low_rated"
