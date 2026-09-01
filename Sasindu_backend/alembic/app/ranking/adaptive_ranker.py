import numpy as np

from app.ranking.features import CandidateFeatures
from app.ranking.linucb import LinUCB
from app.ranking.static_ranker import ScoredCandidate, StaticRanker
from app.ranking.weight_profiles import ARMS


class AdaptiveRanker:
    def __init__(self, context_dim: int, alpha: float = 1.0):
        self.bandit = LinUCB(n_arms=len(ARMS), context_dim=context_dim, alpha=alpha)
        self._static_ranker = StaticRanker()

    def rank(self, context: np.ndarray, features: list[CandidateFeatures]) -> tuple[list[ScoredCandidate], int]:
        arm_index = self.bandit.select_arm(context)
        weights = ARMS[arm_index]
        scored = self._static_ranker.rank(features, weights=weights)
        return scored, arm_index

    def record_feedback(self, context: np.ndarray, arm_index: int, reward: float) -> None:
        self.bandit.update(arm_index, context, reward)
