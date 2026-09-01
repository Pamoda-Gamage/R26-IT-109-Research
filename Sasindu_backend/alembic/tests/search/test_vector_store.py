import pytest

from app.search.vector_store import VectorStore


@pytest.fixture
def store(tmp_path):
    return VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test_providers")


def test_upsert_and_query_returns_relevant_hit(store):
    store.upsert(
        ids=["p1", "p2"],
        texts=["Emergency plumbing repair, available 24/7", "Wedding photography and event coverage"],
        metadatas=[
            {"service_type": "plumbing", "region": "colombo-01"},
            {"service_type": "photography", "region": "colombo-02"},
        ],
    )
    hits = store.query("urgent pipe leak fix needed now", top_k=2)
    assert hits[0].id == "p1"


def test_query_respects_metadata_filter(store):
    store.upsert(
        ids=["p1", "p2"],
        texts=["Emergency plumbing repair", "Non-emergency plumbing maintenance"],
        metadatas=[
            {"service_type": "plumbing", "region": "colombo-01"},
            {"service_type": "plumbing", "region": "colombo-02"},
        ],
    )
    hits = store.query("plumbing service", top_k=5, where={"region": "colombo-02"})
    assert {h.id for h in hits} == {"p2"}


def test_query_respects_multi_key_metadata_filter(store):
    """Chroma rejects a flat multi-key where dict outright ('exactly one operator'
    error) -- this must be wrapped into $and internally by VectorStore.query."""
    store.upsert(
        ids=["p1", "p2", "p3"],
        texts=["Emergency plumbing repair", "Non-emergency plumbing maintenance", "Emergency electrical repair"],
        metadatas=[
            {"service_type": "plumbing", "region": "colombo-01"},
            {"service_type": "plumbing", "region": "colombo-02"},
            {"service_type": "electrical", "region": "colombo-01"},
        ],
    )
    hits = store.query("emergency service", top_k=5, where={"service_type": "plumbing", "region": "colombo-01"})
    assert {h.id for h in hits} == {"p1"}
