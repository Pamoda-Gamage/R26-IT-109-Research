from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine = create_async_engine(get_settings().database_url, echo=False)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session


def new_session() -> AsyncSession:
    """Construct a session directly, without the get_session() context-manager wrapper.

    Needed where a zero-arg factory must hand out a fresh session per call (e.g. the
    Coordinator's per-node session_factory in Phase 8) rather than entering/exiting an
    async context per call. Caller is responsible for closing it."""
    return _session_factory()
