import numpy as np

from app.ranking.linucb import LinUCB


def test_select_arm_returns_valid_index():
    bandit = LinUCB(n_arms=4, context_dim=3, alpha=1.0)
    context = np.array([1.0, 0.0, 0.5])
    arm = bandit.select_arm(context)
    assert 0 <= arm < 4


def test_exploration_bonus_rotates_through_untried_arms_as_pulled_arms_gain_evidence():
    """With alpha > 0, all arms start equally attractive (identity A, zero b), so the
    first pull always ties and deterministically picks arm 0 -- that's correct argmax
    tie-breaking, not a bug. Real LinUCB exploration only emerges once update() is
    interleaved with select_arm(): pulling an arm shrinks its confidence bound (A grows),
    so *other*, still-untouched arms become relatively more attractive on the next round.
    A pure select-with-no-update loop can never explore, since every arm stays tied
    forever -- that would be the actual bug to watch for."""
    bandit = LinUCB(n_arms=4, context_dim=2, alpha=2.0)
    context = np.array([1.0, 1.0])
    visited = set()
    for _ in range(20):
        arm = bandit.select_arm(context)
        visited.add(arm)
        bandit.update(arm, context, reward=1.0)
    assert len(visited) == 4


def test_update_shifts_preference_toward_rewarded_arm():
    bandit = LinUCB(n_arms=2, context_dim=2, alpha=0.1)
    context = np.array([1.0, 1.0])

    for _ in range(50):
        bandit.update(arm_index=0, context=context, reward=1.0)
        bandit.update(arm_index=1, context=context, reward=0.0)

    chosen = bandit.select_arm(context)
    assert chosen == 0


def test_observation_count_starts_at_zero_and_grows_with_updates():
    bandit = LinUCB(n_arms=2, context_dim=2, alpha=1.0)
    context = np.array([1.0, 0.0])

    assert bandit.observation_count(0) == 0
    bandit.update(arm_index=0, context=context, reward=1.0)
    assert bandit.observation_count(0) == 1
    assert bandit.observation_count(1) == 0
