import numpy as np
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.availability.simulator import run_simulator_tick
from app.db.base import Base
from app.db.models.provider import Provider
from app.db.models.provider_state import ProviderStateHistory


@pytest.fixture
async def session_with_providers():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        providers = [
            Provider(
                name=f"P{i}",
                service_type="plumbing",
                region="colombo-01",
                lat=6.9,
                lon=79.8,
                rating=4.0,
                base_response_speed=15.0,
                profile_text="x",
            )
            for i in range(20)
        ]
        s.add_all(providers)
        await s.commit()
        for p in providers:
            s.add(ProviderStateHistory(provider_id=p.id, status="online"))
        await s.commit()
        yield s


async def test_tick_writes_at_least_one_state_change(session_with_providers):
    changed = await run_simulator_tick(session_with_providers, rng=np.random.default_rng(1))
    assert changed >= 1


async def test_tick_only_appends_never_deletes_history(session_with_providers):
    result = await session_with_providers.execute(select(func.count()).select_from(ProviderStateHistory))
    before = result.scalar_one()
    await run_simulator_tick(session_with_providers, rng=np.random.default_rng(1))
    result = await session_with_providers.execute(select(func.count()).select_from(ProviderStateHistory))
    after = result.scalar_one()
    assert after > before
