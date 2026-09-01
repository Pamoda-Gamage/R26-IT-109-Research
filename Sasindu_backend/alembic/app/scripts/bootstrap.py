"""Idempotent startup prerequisites: run once per container start, but each
step checks live state first and skips itself if already satisfied. Safe to
run on every container start (dev loop, restart, redeploy) without redoing
expensive work (embedding 150 profiles, re-fetching the OSM graph, etc.)."""

import asyncio
import subprocess
import time
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.models.provider import Provider
from app.db.session import get_session
from app.routing.graph_loader import load_graph_from_point
from app.scripts.ingest_embeddings import CHROMA_DIR, ingest
from app.scripts.seed_providers import seed_providers

_COLOMBO_CENTER = (6.9271, 79.8612)
_GRAPH_CACHE = Path(__file__).resolve().parent.parent.parent / "data" / "graphs" / "demo_city.graphml"
_EXPECTED_PROVIDER_COUNT = 100


async def wait_for_db(timeout_s: float = 60.0) -> None:
    engine = create_async_engine(get_settings().database_url)
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    try:
        while time.monotonic() < deadline:
            try:
                async with engine.connect():
                    print("[bootstrap] database is reachable")
                    return
            except Exception as exc:  # noqa: BLE001 -- retry on any connect failure until timeout
                last_error = exc
                await asyncio.sleep(1.0)
    finally:
        await engine.dispose()
    raise RuntimeError(f"database not reachable after {timeout_s}s: {last_error}")


def ensure_migrations() -> None:
    print("[bootstrap] alembic upgrade head (no-op if already at head)")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


async def ensure_seeded() -> None:
    async with get_session() as session:
        count = (await session.execute(select(func.count()).select_from(Provider))).scalar_one()

    if count == _EXPECTED_PROVIDER_COUNT:
        print(f"[bootstrap] providers already seeded ({count} rows) -- skipping")
        return

    print(f"[bootstrap] found {count} provider rows, expected {_EXPECTED_PROVIDER_COUNT} -- reseeding cleanly")
    async with get_session() as session:
        created = await seed_providers(session, n=_EXPECTED_PROVIDER_COUNT, seed=get_settings().seed)
    print(f"[bootstrap] seeded {len(created)} providers")


async def ensure_ingested() -> None:
    import chromadb

    async with get_session() as session:
        provider_count = (await session.execute(select(func.count()).select_from(Provider))).scalar_one()

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection("providers", metadata={"hnsw:space": "cosine"})
    chroma_count = collection.count()

    if provider_count > 0 and chroma_count == provider_count:
        print(f"[bootstrap] embeddings already ingested ({chroma_count} vectors) -- skipping")
        return

    print(f"[bootstrap] ingesting embeddings ({chroma_count} vectors present, {provider_count} providers expected)")
    await ingest()


def ensure_graph_cached() -> None:
    already_cached = _GRAPH_CACHE.exists()
    graph = load_graph_from_point(center=_COLOMBO_CENTER, dist_m=6000, cache_path=_GRAPH_CACHE)
    verb = "loaded cached" if already_cached else "fetched and cached"
    print(f"[bootstrap] {verb} OSM road graph ({len(graph.nodes)} nodes) at {_GRAPH_CACHE}")


async def main() -> None:
    await wait_for_db()
    ensure_migrations()
    await ensure_seeded()
    await ensure_ingested()
    ensure_graph_cached()
    print("[bootstrap] all prerequisites satisfied")


if __name__ == "__main__":
    asyncio.run(main())
