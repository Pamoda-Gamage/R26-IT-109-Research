import json
from pathlib import Path

import pandas as pd

from app.search.search_agent import SearchAgent

DEFAULT_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "paraphrase_queries.json"


def run_experiment(search_agent: SearchAgent, queries: list[dict], top_n: int = 10) -> pd.DataFrame:
    rows = []
    for mode in ["hybrid", "semantic_only"]:
        for q in queries:
            results = search_agent.retrieve(
                query=q["query"], service_type=None, region=None, is_emergency=False, mode=mode
            )[:top_n]
            hit = q["expected_provider_id"] in results
            rank = results.index(q["expected_provider_id"]) + 1 if hit else None
            rows.append(
                {
                    "query": q["query"],
                    "mode": mode,
                    "expected_provider_id": q["expected_provider_id"],
                    "hit": hit,
                    "rank": rank,
                }
            )
    return pd.DataFrame(rows)


def main(fixture_path: Path = DEFAULT_FIXTURE_PATH, top_n: int = 10) -> None:
    from app.search.bm25_index import BM25Index
    from app.search.vector_store import VectorStore

    queries = json.loads(fixture_path.read_text())

    chroma_dir = str(Path(__file__).parent.parent.parent / "data" / "chroma")
    vector_store = VectorStore(persist_dir=chroma_dir, collection_name="providers")

    # BM25 needs its own in-memory corpus of the same providers referenced by the fixture
    import asyncio

    from sqlalchemy import select

    from app.db.models.provider import Provider
    from app.db.session import get_session

    async def _load_corpus():
        async with get_session() as session:
            result = await session.execute(select(Provider))
            providers = result.scalars().all()
        return [str(p.id) for p in providers], [p.profile_text for p in providers]

    ids, texts = asyncio.run(_load_corpus())
    bm25_index = BM25Index()
    bm25_index.build(ids, texts)

    search_agent = SearchAgent(vector_store=vector_store, bm25_index=bm25_index)
    df = run_experiment(search_agent, queries, top_n=top_n)

    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    df.to_csv(out_dir / "exp3_retrieval_recall.csv", index=False)

    for mode in ["hybrid", "semantic_only"]:
        recall = df[df["mode"] == mode]["hit"].mean()
        print(f"{mode}: recall@{top_n}={recall:.3f}")


if __name__ == "__main__":
    main()
