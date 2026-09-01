import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.availability.availability_agent import AvailabilityAgent
from app.db.base import Base
from app.db.models.provider import Provider
from app.db.models.provider_state import ProviderStateHistory


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s


async def _make_provider(session, status_sequence):
    p = Provider(
        name="P",
        service_type="plumbing",
        region="colombo-01",
        lat=6.9,
        lon=79.8,
        rating=4.0,
        base_response_speed=15.0,
        profile_text="x",
    )
    session.add(p)
    await session.commit()
    # commit each status change separately, matching real usage: the simulator writes
    # one state-history row per provider per tick, each its own transaction, so
    # `changed_at` timestamps are naturally distinct. Batch-committing them all at once
    # (as a single transaction) makes server_default=func.now() identical across rows,
    # breaking "latest row = current status" ordering -- not a realistic scenario.
    for status in status_sequence:
        session.add(ProviderStateHistory(provider_id=p.id, status=status))
        await session.commit()
    return p


async def test_offline_provider_is_filtered_out(session):
    online_p = await _make_provider(session, ["online"])
    offline_p = await _make_provider(session, ["online", "offline"])

    agent = AvailabilityAgent()
    results = await agent.filter_and_score(session, [str(online_p.id), str(offline_p.id)])

    assert str(online_p.id) in results
    assert str(offline_p.id) not in results


async def test_provider_with_no_history_defaults_to_available(session):
    """Before the simulator has ever ticked for a provider, it has zero history rows.
    simulator.py's _current_state treats that as an implicit "online" default -- the
    agent must match that, not exclude every provider whenever the simulator hasn't
    run yet (e.g. on first boot before its background loop's first tick)."""
    p = Provider(
        name="P",
        service_type="plumbing",
        region="colombo-01",
        lat=6.9,
        lon=79.8,
        rating=4.0,
        base_response_speed=15.0,
        profile_text="x",
    )
    session.add(p)
    await session.commit()

    agent = AvailabilityAgent()
    results = await agent.filter_and_score(session, [str(p.id)])

    assert str(p.id) in results
    assert results[str(p.id)].status == "online"


async def test_frequently_busy_provider_has_lower_acceptance_probability(session):
    stable_p = await _make_provider(session, ["online"] * 5)
    flaky_p = await _make_provider(session, ["online", "busy", "online", "busy", "busy"])

    agent = AvailabilityAgent()
    results = await agent.filter_and_score(session, [str(stable_p.id), str(flaky_p.id)])

    assert results[str(stable_p.id)].acceptance_probability > results[str(flaky_p.id)].acceptance_probability
