import pytest  # type: ignore[import-not-found]
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # type: ignore[import-not-found]

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


async def test_provider_roundtrip(session):
    p = Provider(
        name="Test Provider",
        service_type="plumbing",
        region="colombo-01",
        lat=6.9271,
        lon=79.8612,
        rating=4.5,
        base_response_speed=15.0,
        profile_text="Fast plumbing service in Colombo",
    )
    session.add(p)
    await session.commit()
    result = await session.get(Provider, p.id)
    assert result.name == "Test Provider"
    assert result.reliability_alpha == 1.0


async def test_provider_state_history_links_to_provider(session):
    p = Provider(
        name="P2",
        service_type="electrical",
        region="colombo-02",
        lat=6.9,
        lon=79.8,
        rating=4.0,
        base_response_speed=20.0,
        profile_text="x",
    )
    session.add(p)
    await session.commit()
    state = ProviderStateHistory(provider_id=p.id, status="online")
    session.add(state)
    await session.commit()
    assert state.status == "online"
