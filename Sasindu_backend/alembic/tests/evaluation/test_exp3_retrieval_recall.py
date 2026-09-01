import pytest

from app.search.bm25_index import BM25Index
from app.search.search_agent import SearchAgent
from app.search.vector_store import VectorStore
from evaluation.experiments.exp3_retrieval_recall import run_experiment


@pytest.fixture
def agent(tmp_path):
    store = VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    bm25 = BM25Index()
    ids = ["p1", "p2"]
    texts = ["Emergency plumbing leak repair available 24/7", "Certified electrician for wiring and panel issues"]
    metas = [
        {"service_type": "plumbing", "region": "colombo-01"},
        {"service_type": "electrical", "region": "colombo-01"},
    ]
    store.upsert(ids, texts, metas)
    bm25.build(ids, texts)
    return SearchAgent(vector_store=store, bm25_index=bm25)


def test_run_experiment_computes_hit_and_rank_per_query(agent):
    queries = [
        {"query": "my pipes are leaking and I need someone urgently", "expected_provider_id": "p1"},
        {"query": "power went out, need someone to check the wiring", "expected_provider_id": "p2"},
    ]
    df = run_experiment(agent, queries, top_n=5)
    assert set(df.columns) == {"query", "mode", "expected_provider_id", "hit", "rank"}
    assert df["hit"].all()


def test_hybrid_mode_recall_is_at_least_semantic_only_recall(agent):
    queries = [{"query": "my pipes are leaking and I need someone urgently", "expected_provider_id": "p1"}]
    df = run_experiment(agent, queries, top_n=5)
    hybrid_recall = df[df["mode"] == "hybrid"]["hit"].mean()
    semantic_recall = df[df["mode"] == "semantic_only"]["hit"].mean()
    assert hybrid_recall >= semantic_recall
