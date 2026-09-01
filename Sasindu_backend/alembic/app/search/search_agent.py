from typing import Literal

from app.search.bm25_index import BM25Index
from app.search.fusion import reciprocal_rank_fusion
from app.search.vector_store import VectorStore

NORMAL_TOP_N = 25
EMERGENCY_TOP_N = 10


class SearchAgent:
    def __init__(self, vector_store: VectorStore, bm25_index: BM25Index):
        self._vector_store = vector_store
        self._bm25_index = bm25_index

    def retrieve(
        self,
        query: str,
        service_type: str | None,
        region: str | None,
        is_emergency: bool,
        mode: Literal["hybrid", "semantic_only"] = "hybrid",
    ) -> list[str]:
        top_n = EMERGENCY_TOP_N if is_emergency else NORMAL_TOP_N
        where = {}
        if service_type:
            where["service_type"] = service_type
        if region:
            where["region"] = region

        dense_hits = self._vector_store.query(query, top_k=top_n * 2, where=where or None)

        if mode == "semantic_only":
            return [h.id for h in dense_hits[:top_n]]

        sparse_hits = self._bm25_index.query(query, top_k=top_n * 2)
        if where:
            allowed_ids = {h.id for h in dense_hits}
            sparse_hits = [h for h in sparse_hits if h.id in allowed_ids]

        fused = reciprocal_rank_fusion([dense_hits, sparse_hits])
        return [h.id for h in fused[:top_n]]
