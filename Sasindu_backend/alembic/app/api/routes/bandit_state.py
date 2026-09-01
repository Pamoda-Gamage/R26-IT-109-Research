from fastapi import APIRouter, Depends

from app.api.dependencies import get_adaptive_ranker
from app.ranking.adaptive_ranker import AdaptiveRanker
from app.ranking.weight_profiles import ARM_NAMES

router = APIRouter()


def build_bandit_state(ranker: AdaptiveRanker) -> dict:
    state = {}
    for index, name in enumerate(ARM_NAMES):
        theta = ranker.bandit.theta(index)
        state[name] = {"theta": theta.tolist(), "observation_count": ranker.bandit.observation_count(index)}
    return state


@router.get("/bandit/state")
async def get_bandit_state(ranker: AdaptiveRanker = Depends(get_adaptive_ranker)):
    return build_bandit_state(ranker)
