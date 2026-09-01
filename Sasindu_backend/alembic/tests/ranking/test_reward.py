from app.ranking.reward import compute_reward


def test_top_3_selection_gets_full_reward():
    assert compute_reward(selected_rank=1) == 1.0
    assert compute_reward(selected_rank=3) == 1.0


def test_lower_rank_gets_partial_reward():
    reward = compute_reward(selected_rank=10)
    assert 0.0 < reward < 1.0


def test_abandonment_gets_zero_reward():
    assert compute_reward(selected_rank=None) == 0.0


def test_reward_decreases_monotonically_with_rank():
    r5 = compute_reward(selected_rank=5)
    r15 = compute_reward(selected_rank=15)
    assert r5 > r15
