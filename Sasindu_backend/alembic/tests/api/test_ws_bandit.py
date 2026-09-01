from fastapi.testclient import TestClient

from app.api.main import app


def test_ws_bandit_pushes_update_after_feedback():
    client = TestClient(app)
    with client.websocket_connect("/ws/bandit") as ws:
        client.post("/feedback", json={"context": [1.0, 0, 0, 0, 0, 0], "arm_index": 0, "selected_rank": 1})
        message = ws.receive_json()
        assert "balanced_pp1_baseline" in message
