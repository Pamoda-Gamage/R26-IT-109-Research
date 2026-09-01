from app.search.vector_store import RankedHit


def reciprocal_rank_fusion(ranked_lists: list[list[RankedHit]], k: int = 60) -> list[RankedHit]:
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, hit in enumerate(ranked_list, start=1):
            scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (k + rank)

    fused = [RankedHit(id=doc_id, score=score) for doc_id, score in scores.items()]
    fused.sort(key=lambda h: h.score, reverse=True)
    return fused
