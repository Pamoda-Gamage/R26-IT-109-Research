from app.search.bm25_index import BM25Index


def test_bm25_ranks_exact_keyword_match_first():
    index = BM25Index()
    index.build(
        ids=["p1", "p2"],
        texts=["locksmith emergency lockout service", "general handyman odd jobs"],
    )
    hits = index.query("locksmith lockout", top_k=2)
    assert hits[0].id == "p1"
