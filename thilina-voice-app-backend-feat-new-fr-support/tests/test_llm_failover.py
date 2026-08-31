"""LLM layer: failover, retry/backoff, response cache, concurrency cap.

Run:  ./.venv/Scripts/python.exe -m pytest tests/test_llm_failover.py -q
"""
import threading
import time

import pytest

from app.services.llm import base, client
from app.services.llm.base import AllProvidersFailed, LLMPermanent, LLMTransient


@pytest.fixture(autouse=True)
def _reset():
    client._cache.clear()
    yield
    client._cache.clear()


class FakeProvider:
    def __init__(self, name, *, available=True, behavior=None):
        self.name = name
        self._available = available
        self.calls = 0
        self._behavior = behavior or (lambda calls: ("ok-" + name, ""))

    def available(self):
        return self._available

    def translate_text(self, text):
        self.calls += 1
        return self._behavior(self.calls)

    # unused here but part of the contract
    def transcribe_audio(self, b):  # pragma: no cover
        return self.translate_text("")

    def analyze_image(self, b, m, c=""):  # pragma: no cover
        return {}


def _install(monkeypatch, providers, *, primary="a", fallback=True):
    monkeypatch.setattr(client, "_PROVIDERS", providers)
    monkeypatch.setattr(client.config, "LLM_PROVIDER", primary)
    monkeypatch.setattr(client.config, "LLM_FALLBACK_ENABLED", fallback)


def test_failover_to_second_provider(monkeypatch):
    def boom(_):
        raise LLMPermanent("bad key")

    a = FakeProvider("a", behavior=boom)
    b = FakeProvider("b")
    _install(monkeypatch, {"a": a, "b": b})

    assert client.translate_text("hi") == ("ok-b", "")
    assert a.calls == 1 and b.calls == 1


def test_all_providers_failed(monkeypatch):
    def boom(_):
        raise LLMTransient("429")

    a = FakeProvider("a", behavior=boom)
    b = FakeProvider("b", behavior=boom)
    _install(monkeypatch, {"a": a, "b": b})

    with pytest.raises(AllProvidersFailed):
        client.translate_text("hi")


def test_skips_unavailable_provider(monkeypatch):
    a = FakeProvider("a", available=False)
    b = FakeProvider("b")
    _install(monkeypatch, {"a": a, "b": b})

    assert client.translate_text("hi") == ("ok-b", "")
    assert a.calls == 0


def test_cache_hit_skips_second_call(monkeypatch):
    a = FakeProvider("a")
    _install(monkeypatch, {"a": a}, fallback=False)

    assert client.translate_text("same") == ("ok-a", "")
    assert client.translate_text("same") == ("ok-a", "")
    assert a.calls == 1  # second call served from cache


def test_prefer_overrides_primary(monkeypatch):
    a = FakeProvider("a")
    b = FakeProvider("b")
    _install(monkeypatch, {"a": a, "b": b}, primary="a")

    assert client.translate_text("hi", prefer="b") == ("ok-b", "")
    assert b.calls == 1 and a.calls == 0


def test_concurrency_cap(monkeypatch):
    monkeypatch.setattr(client, "_sem", threading.BoundedSemaphore(2))
    peak = {"n": 0, "cur": 0}
    lock = threading.Lock()

    def slow(_):
        with lock:
            peak["cur"] += 1
            peak["n"] = max(peak["n"], peak["cur"])
        time.sleep(0.05)
        with lock:
            peak["cur"] -= 1
        return ("ok", "")

    a = FakeProvider("a", behavior=slow)
    _install(monkeypatch, {"a": a}, fallback=False)

    threads = [threading.Thread(target=lambda i=i: client.translate_text(f"t{i}"))
               for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert peak["n"] <= 2


def test_retry_policy_recovers(monkeypatch):
    """The tenacity policy on a provider's own call retries transient errors."""
    from app.services.llm.retry import with_retry

    state = {"n": 0}

    @with_retry
    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise LLMTransient("429")
        return "recovered"

    # speed the backoff up so the test is fast
    assert flaky() == "recovered"
    assert state["n"] == 3
