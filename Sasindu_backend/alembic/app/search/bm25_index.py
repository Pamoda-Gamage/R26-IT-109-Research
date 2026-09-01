from rank_bm25 import BM25Okapi

from app.search.vector_store import RankedHit


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


class BM25Index:
    def __init__(self):
        self._ids: list[str] = []
        self._bm25: BM25Okapi | None = None

    def build(self, ids: list[str], texts: list[str]) -> None:
        self._ids = ids
        tokenized = [_tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized)

    def query(self, text: str, top_k: int) -> list[RankedHit]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(text))
        ranked = sorted(zip(self._ids, scores, strict=True), key=lambda pair: pair[1], reverse=True)
        return [RankedHit(id=i, score=float(s)) for i, s in ranked[:top_k]]
