from app.search.fusion import reciprocal_rank_fusion
from app.search.vector_store import RankedHit


def test_rrf_boosts_items_that_rank_well_in_both_lists():
    dense = [RankedHit("a", 0.9), RankedHit("b", 0.8), RankedHit("c", 0.7)]
    sparse = [RankedHit("b", 5.0), RankedHit("a", 4.0), RankedHit("d", 3.0)]

    fused = reciprocal_rank_fusion([dense, sparse])
    fused_ids = [h.id for h in fused]

    assert fused_ids.index("a") < fused_ids.index("c")
    assert fused_ids.index("b") < fused_ids.index("d")


def test_rrf_score_matches_formula():
    dense = [RankedHit("a", 1.0)]
    sparse = [RankedHit("a", 1.0)]
    fused = reciprocal_rank_fusion([dense, sparse], k=60)
    expected = 1 / (60 + 1) + 1 / (60 + 1)
    assert abs(fused[0].score - expected) < 1e-9
