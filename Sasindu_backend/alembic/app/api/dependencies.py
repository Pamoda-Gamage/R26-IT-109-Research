from functools import lru_cache

from app.ranking.adaptive_ranker import AdaptiveRanker

CONTEXT_DIM = 6  # [is_emergency, early_morning, morning_peak, midday, evening_peak, night]


@lru_cache
def get_adaptive_ranker() -> AdaptiveRanker:
    # alpha=0.5 tuned in Phase 6: alpha=1.0 had a ~4% chance of the bandit
    # permanently locking onto a suboptimal arm early; 0.5 measured 0/300 in a
    # seed sweep. See tests/ranking/test_convergence.py.
    return AdaptiveRanker(context_dim=CONTEXT_DIM, alpha=0.5)
