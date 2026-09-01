from app.ranking.static_ranker import PP1_BASELINE_WEIGHTS
from app.ranking.weight_profiles import ARM_NAMES, ARMS


def test_arms_and_names_are_parallel_and_nonempty():
    assert len(ARMS) == len(ARM_NAMES)
    assert len(ARMS) >= 4


def test_every_arm_weights_sum_to_one():
    for arm in ARMS:
        total = arm.rating + arm.availability + arm.reliability + arm.response_speed + arm.eta_score
        assert abs(total - 1.0) < 1e-9


def test_pp1_baseline_is_one_of_the_arms():
    assert PP1_BASELINE_WEIGHTS in ARMS
