import pytest

from app.search.bm25_index import BM25Index
from app.search.search_agent import SearchAgent
from app.search.vector_store import VectorStore


@pytest.fixture
def agent(tmp_path):
    store = VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    bm25 = BM25Index()
    ids = ["p1", "p2", "p3"]
    texts = [
        "Emergency 24/7 plumbing leak repair in Colombo",
        "Standard plumbing maintenance and installation",
        "Wedding photography services",
    ]
    metas = [
        {"service_type": "plumbing", "region": "colombo-01"},
        {"service_type": "plumbing", "region": "colombo-01"},
        {"service_type": "photography", "region": "colombo-01"},
    ]
    store.upsert(ids, texts, metas)
    bm25.build(ids, texts)
    return SearchAgent(vector_store=store, bm25_index=bm25)


def test_retrieve_filters_out_irrelevant_service_type(agent):
    results = agent.retrieve("burst pipe emergency", service_type="plumbing", region=None, is_emergency=False)
    assert "p3" not in results


def test_retrieve_caps_at_10_for_emergency(agent):
    results = agent.retrieve("urgent leak", service_type=None, region=None, is_emergency=True)
    assert len(results) <= 10


def test_paraphrased_query_still_finds_relevant_provider(agent):
    """Core requirement: semantic retrieval must survive paraphrasing that keyword search would miss."""
    results = agent.retrieve(
        "my pipes are leaking and I need someone urgently", service_type="plumbing", region=None, is_emergency=True
    )
    assert "p1" in results
