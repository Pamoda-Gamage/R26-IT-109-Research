import numpy as np


class LinUCB:
    """Disjoint LinUCB contextual bandit (Li et al., 2010)."""

    def __init__(self, n_arms: int, context_dim: int, alpha: float = 1.0):
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha
        self._A = [np.eye(context_dim) for _ in range(n_arms)]
        self._b = [np.zeros(context_dim) for _ in range(n_arms)]

    def select_arm(self, context: np.ndarray) -> int:
        best_arm, best_score = 0, -np.inf
        for arm in range(self.n_arms):
            A_inv = np.linalg.inv(self._A[arm])
            theta = A_inv @ self._b[arm]
            expected = theta @ context
            confidence = self.alpha * np.sqrt(context @ A_inv @ context)
            ucb = expected + confidence
            if ucb > best_score:
                best_score, best_arm = ucb, arm
        return best_arm

    def update(self, arm_index: int, context: np.ndarray, reward: float) -> None:
        self._A[arm_index] += np.outer(context, context)
        self._b[arm_index] += reward * context

    def theta(self, arm_index: int) -> np.ndarray:
        """Exposes the learned linear weight vector for a given arm — used by GET /bandit/state (Phase 7)."""
        A_inv = np.linalg.inv(self._A[arm_index])
        return A_inv @ self._b[arm_index]

    def observation_count(self, arm_index: int) -> int:
        """Pseudo-observation count for an arm: trace(A) - context_dim recovers the
        number of rank-1 updates folded into A since it started as the identity matrix.
        Used by GET /bandit/state (Phase 7) to show learning progress per arm."""
        return max(0, int(round(self._A[arm_index].trace() - self.context_dim)))
