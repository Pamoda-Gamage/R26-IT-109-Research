import numpy as np
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import CONTEXT_DIM, get_adaptive_ranker
from app.api.routes.bandit_state import build_bandit_state
from app.api.routes.ws_bandit import broadcast_bandit_state
from app.ranking.adaptive_ranker import AdaptiveRanker
from app.ranking.static_ranker import PP1_BASELINE_WEIGHTS
from app.ranking.weight_profiles import ARM_NAMES, ARMS
from app.routing.traffic import TIME_SLOTS

router = APIRouter()

# Context encoding matches Phase 8's ranking_node exactly:
# [is_emergency, early_morning, morning_peak, midday, evening_peak, night] -> CONTEXT_DIM (6)
EMERGENCY_PREFERRED_ARM = ARM_NAMES.index("eta_heavy")
NORMAL_PREFERRED_ARM = ARM_NAMES.index("rating_heavy")
BASELINE_ARM_INDEX = ARMS.index(PP1_BASELINE_WEIGHTS)


def _build_context(is_emergency: bool, time_slot: str) -> np.ndarray:
    onehot = [1.0 if time_slot == slot else 0.0 for slot in TIME_SLOTS]
    return np.array([1.0 if is_emergency else 0.0, *onehot])


assert len(_build_context(False, TIME_SLOTS[0])) == CONTEXT_DIM


class SimulateRequest(BaseModel):
    n: int = 100


def _simulated_reward(is_emergency: bool, arm_index: int, rng: np.random.Generator) -> float:
    preferred = EMERGENCY_PREFERRED_ARM if is_emergency else NORMAL_PREFERRED_ARM
    base_p = 0.85 if arm_index == preferred else 0.25
    return float(rng.random() < base_p)


@router.post("/simulate/batch")
async def simulate_batch(payload: SimulateRequest, ranker: AdaptiveRanker = Depends(get_adaptive_ranker)):
    rng = np.random.default_rng()
    cumulative_adaptive, cumulative_static = 0.0, 0.0

    for _ in range(payload.n):
        is_emergency = bool(rng.random() < 0.5)
        time_slot = str(rng.choice(TIME_SLOTS))
        context = _build_context(is_emergency, time_slot)

        chosen_arm = ranker.bandit.select_arm(context)
        adaptive_reward = _simulated_reward(is_emergency, chosen_arm, rng)
        ranker.record_feedback(context, chosen_arm, adaptive_reward)
        cumulative_adaptive += adaptive_reward

        static_reward = _simulated_reward(is_emergency, BASELINE_ARM_INDEX, rng)
        cumulative_static += static_reward

    await broadcast_bandit_state(build_bandit_state(ranker))

    return {
        "requests_fired": payload.n,
        "cumulative_reward_adaptive": cumulative_adaptive,
        "cumulative_reward_static_baseline": cumulative_static,
    }
