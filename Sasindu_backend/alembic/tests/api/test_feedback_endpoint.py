import numpy as np
from fastapi.testclient import TestClient

from app.api.dependencies import CONTEXT_DIM, get_adaptive_ranker
from app.api.main import app


def test_feedback_updates_bandit_state():
    client = TestClient(app)
    ranker = get_adaptive_ranker()
    context = [1.0] + [0.0] * (CONTEXT_DIM - 1)

    response = client.post(
        "/feedback",
        json={
            "context": context,
            "arm_index": 1,
            "selected_rank": 1,
        },
    )
    assert response.status_code == 200

    theta = ranker.bandit.theta(1)
    assert not np.allclose(theta, 0.0)


def test_feedback_rejects_out_of_range_arm_index():
    client = TestClient(app)
    response = client.post(
        "/feedback",
        json={
            "context": [0.0] * CONTEXT_DIM,
            "arm_index": 999,
            "selected_rank": 1,
        },
    )
    assert response.status_code == 422
