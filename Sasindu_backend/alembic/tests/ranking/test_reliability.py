from app.ranking.reliability import update_reliability


def test_positive_outcome_increases_alpha_not_beta():
    alpha, beta = update_reliability(alpha=1.0, beta=1.0, reward=1.0)
    assert alpha == 2.0
    assert beta == 1.0


def test_negative_outcome_increases_beta_not_alpha():
    alpha, beta = update_reliability(alpha=1.0, beta=1.0, reward=0.0)
    assert alpha == 1.0
    assert beta == 2.0


def test_partial_reward_splits_proportionally():
    alpha, beta = update_reliability(alpha=1.0, beta=1.0, reward=0.5)
    assert alpha == 1.5
    assert beta == 1.5


def test_posterior_mean_moves_toward_repeated_evidence():
    alpha, beta = 1.0, 1.0
    for _ in range(20):
        alpha, beta = update_reliability(alpha, beta, reward=1.0)
    mean = alpha / (alpha + beta)
    assert mean > 0.9
