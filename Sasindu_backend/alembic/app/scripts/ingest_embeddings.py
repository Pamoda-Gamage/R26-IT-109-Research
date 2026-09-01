from pathlib import Path

from sqlalchemy import select

from app.db.models.provider import Provider
from app.db.session import get_session
from app.search.bm25_index import BM25Index
from app.search.vector_store import VectorStore

CHROMA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma")


async def ingest() -> tuple[VectorStore, BM25Index]:
    async with get_session() as session:
        result = await session.execute(select(Provider))
        providers = result.scalars().all()

    ids = [str(p.id) for p in providers]
    texts = [p.profile_text for p in providers]
    metadatas = [{"service_type": p.service_type, "region": p.region} for p in providers]

    store = VectorStore(persist_dir=CHROMA_DIR, collection_name="providers")
    store.reset()
    store.upsert(ids, texts, metadatas)

    bm25 = BM25Index()
    bm25.build(ids, texts)

    print(f"Ingested {len(ids)} provider profiles into vector store + BM25 index")
    return store, bm25


if __name__ == "__main__":
    import asyncio

    asyncio.run(ingest())
