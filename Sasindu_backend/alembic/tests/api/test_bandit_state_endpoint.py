from fastapi.testclient import TestClient

from app.api.main import app
from app.ranking.weight_profiles import ARM_NAMES


def test_bandit_state_returns_one_entry_per_arm():
    client = TestClient(app)
    response = client.get("/bandit/state")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == set(ARM_NAMES)
    for arm_name in ARM_NAMES:
        assert "theta" in body[arm_name]
        assert "observation_count" in body[arm_name]
