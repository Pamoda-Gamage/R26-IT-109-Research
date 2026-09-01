import uuid

import pytest
from fastapi.testclient import TestClient

import app.api.routes.request as request_route
from app.coordinator.graph import build_graph
from tests.coordinator.conftest import (
    FakeAdaptiveRanker,
    FakeAvailabilityAgent,
    FakeContextAgent,
    FakeDistanceAgent,
    FakeProvider,
    FakeSearchAgent,
)


@pytest.fixture(autouse=True)
def fake_compiled_graph(monkeypatch):
    """Injects a graph built entirely from fakes so this test never hits real
    Postgres, Chroma, OSM, or the Anthropic API -- those are exercised by the
    already-passing unit/integration tests for each individual agent."""
    provider_nodes = {"p1": 1, "p2": 2}
    provider_lookup = {
        pid: FakeProvider(rating=4.0, reliability_alpha=5.0, reliability_beta=5.0, base_response_speed=15.0)
        for pid in provider_nodes
    }
    compiled = build_graph(
        context_agent=FakeContextAgent(urgency="emergency"),
        search_agent=FakeSearchAgent(emergency_results=["p1", "p2"]),
        distance_agent=FakeDistanceAgent(),
        availability_agent=FakeAvailabilityAgent(),
        adaptive_ranker=FakeAdaptiveRanker(),
        provider_nodes=provider_nodes,
        source_node_resolver=lambda state: 0,
        session_factory=lambda: None,
        provider_lookup_factory=lambda: provider_lookup,
    )

    async def _fake_get_compiled_graph():
        return compiled

    monkeypatch.setattr(request_route, "_get_compiled_graph", _fake_get_compiled_graph)


@pytest.fixture(autouse=True)
def no_db_write(monkeypatch):
    """The trace-persistence write itself (RequestLog INSERT) is a straightforward,
    already-covered SQLAlchemy pattern (see tests/test_models.py) -- stub it here so
    this test doesn't need a live Postgres connection either."""
    from contextlib import asynccontextmanager

    class _FakeSession:
        def add(self, obj):
            pass

        async def commit(self):
            pass

    @asynccontextmanager
    async def _fake_get_session():
        yield _FakeSession()

    monkeypatch.setattr(request_route, "get_session", _fake_get_session)


def test_request_endpoint_returns_trace_and_persists_it():
    client = TestClient(_app())
    response = client.post(
        "/request",
        json={
            "raw_text": "need a plumber urgently, pipe burst",
            "timestamp": "2026-01-01T21:00:00Z",
            "region": "colombo-01",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert uuid.UUID(body["request_id"])
    assert len(body["trace"]) == 5
    assert "chosen_arm" in body


def _app():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(request_route.router)
    return app
