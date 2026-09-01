from pathlib import Path

import numpy as np
import pandas as pd

from app.ranking.adaptive_ranker import AdaptiveRanker
from app.ranking.static_ranker import PP1_BASELINE_WEIGHTS
from app.ranking.weight_profiles import ARM_NAMES, ARMS
from evaluation.stats import bootstrap_ci

EMERGENCY_CONTEXT = np.array([1.0, 0.0])
NORMAL_CONTEXT = np.array([0.0, 1.0])
EMERGENCY_PREFERRED_ARM = ARM_NAMES.index("eta_heavy")
NORMAL_PREFERRED_ARM = ARM_NAMES.index("rating_heavy")
BASELINE_ARM_INDEX = ARMS.index(PP1_BASELINE_WEIGHTS)
BEST_CASE_REWARD_PROB = 0.85  # ground-truth ceiling used for regret calculation

# alpha=0.5 tuned in Phase 6 (tests/ranking/test_convergence.py): alpha=1.0 had a ~4%
# chance of the bandit permanently locking onto a suboptimal arm early; 0.5 measured
# 0/300 failures across a seed sweep.
BANDIT_ALPHA = 0.5


def _simulated_reward(context: np.ndarray, arm_index: int, rng: np.random.Generator) -> float:
    is_emergency = context[0] == 1.0
    preferred = EMERGENCY_PREFERRED_ARM if is_emergency else NORMAL_PREFERRED_ARM
    base_p = BEST_CASE_REWARD_PROB if arm_index == preferred else 0.25
    return float(rng.random() < base_p)


def run_experiment(n_rounds: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ranker = AdaptiveRanker(context_dim=2, alpha=BANDIT_ALPHA)

    rows = []
    cumulative_regret_adaptive, cumulative_regret_static = 0.0, 0.0
    for round_idx in range(n_rounds):
        context = EMERGENCY_CONTEXT if rng.random() < 0.5 else NORMAL_CONTEXT
        context_label = "emergency" if context[0] == 1.0 else "normal"

        chosen_arm = ranker.bandit.select_arm(context)
        adaptive_reward = _simulated_reward(context, chosen_arm, rng)
        ranker.record_feedback(context, chosen_arm, adaptive_reward)
        cumulative_regret_adaptive += BEST_CASE_REWARD_PROB - adaptive_reward
        rows.append(
            {
                "round": round_idx,
                "condition": "adaptive",
                "context": context_label,
                "reward": adaptive_reward,
                "cumulative_regret": cumulative_regret_adaptive,
            }
        )

        static_reward = _simulated_reward(context, BASELINE_ARM_INDEX, rng)
        cumulative_regret_static += BEST_CASE_REWARD_PROB - static_reward
        rows.append(
            {
                "round": round_idx,
                "condition": "static_baseline",
                "context": context_label,
                "reward": static_reward,
                "cumulative_regret": cumulative_regret_static,
            }
        )

    return pd.DataFrame(rows)


def main(n_rounds: int = 1000, seed: int = 42) -> None:
    df = run_experiment(n_rounds, seed)
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    df.to_csv(out_dir / "exp1_adaptive_vs_static.csv", index=False)

    for condition in ["adaptive", "static_baseline"]:
        rewards = df[df.condition == condition]["reward"].tolist()
        mean, lo, hi = bootstrap_ci(rewards, seed=seed)
        final_regret = df[df.condition == condition]["cumulative_regret"].iloc[-1]
        print(
            f"{condition}: acceptance_rate={mean:.3f} CI=[{lo:.3f},{hi:.3f}], "
            f"final_cumulative_regret={final_regret:.1f}"
        )


if __name__ == "__main__":
    main()
