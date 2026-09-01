from fastapi.testclient import TestClient

from app.api.main import app


def test_simulate_batch_returns_cumulative_rewards_for_both_conditions():
    client = TestClient(app)
    response = client.post("/simulate/batch", json={"n": 100})
    assert response.status_code == 200
    body = response.json()
    assert body["requests_fired"] == 100
    assert "cumulative_reward_adaptive" in body
    assert "cumulative_reward_static_baseline" in body


def test_simulate_batch_adaptive_eventually_beats_static_baseline():
    """Literal viva-demo claim: adaptive cumulative reward should overtake the
    static baseline given enough simulated traffic."""
    client = TestClient(app)
    response = client.post("/simulate/batch", json={"n": 800})
    body = response.json()
    assert body["cumulative_reward_adaptive"] >= body["cumulative_reward_static_baseline"]
