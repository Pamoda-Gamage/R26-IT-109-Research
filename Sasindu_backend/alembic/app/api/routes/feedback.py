import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import CONTEXT_DIM, get_adaptive_ranker
from app.api.routes.bandit_state import build_bandit_state
from app.api.routes.ws_bandit import broadcast_bandit_state
from app.ranking.adaptive_ranker import AdaptiveRanker
from app.ranking.reward import compute_reward
from app.ranking.weight_profiles import ARMS

router = APIRouter()


class FeedbackRequest(BaseModel):
    context: list[float] = Field(min_length=CONTEXT_DIM, max_length=CONTEXT_DIM)
    arm_index: int
    selected_rank: int | None = None


@router.post("/feedback")
async def submit_feedback(payload: FeedbackRequest, ranker: AdaptiveRanker = Depends(get_adaptive_ranker)):
    if not 0 <= payload.arm_index < len(ARMS):
        raise HTTPException(status_code=422, detail=f"arm_index must be in [0, {len(ARMS)})")

    reward = compute_reward(payload.selected_rank)
    ranker.record_feedback(np.array(payload.context), payload.arm_index, reward)
    await broadcast_bandit_state(build_bandit_state(ranker))
    return {"reward": reward}
