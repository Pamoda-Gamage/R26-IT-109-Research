import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.provider import Provider
from app.scripts.seed_providers import seed_providers


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s


async def test_seed_creates_at_least_150_providers(session):
    created = await seed_providers(session, n=150, seed=42)
    assert len(created) == 150
    result = await session.execute(select(Provider))
    assert len(result.scalars().all()) == 150


async def test_seed_is_deterministic_given_same_seed(session):
    first = await seed_providers(session, n=20, seed=42)
    first_names = sorted(p.name for p in first)

    engine2 = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine2.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory2 = async_sessionmaker(engine2, expire_on_commit=False)
    async with factory2() as session2:
        second = await seed_providers(session2, n=20, seed=42)
        second_names = sorted(p.name for p in second)

    assert first_names == second_names


async def test_seed_covers_multiple_service_types_and_regions(session):
    created = await seed_providers(session, n=150, seed=42)
    service_types = {p.service_type for p in created}
    regions = {p.region for p in created}
    assert len(service_types) >= 4
    assert len(regions) >= 3
