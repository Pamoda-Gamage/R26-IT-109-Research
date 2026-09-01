from dataclasses import dataclass

import chromadb

from app.search.embeddings import Embedder


@dataclass
class RankedHit:
    id: str
    score: float


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "providers"):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection_name = collection_name
        self._collection = self._client.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})
        self._embedder = Embedder()

    def reset(self) -> None:
        """Drops and recreates the collection -- used before a full re-ingest so stale
        vectors for providers that no longer exist (e.g. after a reseed) don't linger."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(
            self._collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
        embeddings = self._embedder.encode(texts).tolist()
        self._collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    def query(self, text: str, top_k: int, where: dict | None = None) -> list[RankedHit]:
        query_embedding = self._embedder.encode([text])[0].tolist()
        result = self._collection.query(
            query_embeddings=[query_embedding], n_results=top_k, where=_normalize_where(where)
        )
        ids = result["ids"][0]
        distances = result["distances"][0]
        return [RankedHit(id=i, score=1 - d) for i, d in zip(ids, distances, strict=True)]


def _normalize_where(where: dict | None) -> dict | None:
    """Chroma rejects a flat multi-key dict ('exactly one operator' error) — a filter
    on more than one field must be wrapped in an explicit $and."""
    if not where or len(where) <= 1:
        return where
    return {"$and": [{key: value} for key, value in where.items()]}
