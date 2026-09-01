import asyncio

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.availability.state_machine import ProviderStateMachine
from app.db.models.provider import Provider
from app.db.models.provider_state import ProviderStateHistory

_machine = ProviderStateMachine()


async def _current_state(session: AsyncSession, provider_id) -> str:
    stmt = (
        select(ProviderStateHistory.status)
        .where(ProviderStateHistory.provider_id == provider_id)
        .order_by(ProviderStateHistory.changed_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    return row or "online"


async def run_simulator_tick(session: AsyncSession, rng: np.random.Generator) -> int:
    result = await session.execute(select(Provider.id))
    provider_ids = [row[0] for row in result.all()]

    changed = 0
    for provider_id in provider_ids:
        current = await _current_state(session, provider_id)
        new_state = _machine.next_state(current, rng)
        if new_state != current:
            session.add(ProviderStateHistory(provider_id=provider_id, status=new_state))
            changed += 1
    await session.commit()
    return changed


async def run_simulator_loop(interval_seconds: float = 5.0) -> None:
    """Standalone process entrypoint — run independently of the API server
    so availability visibly changes even with zero incoming requests."""
    from app.core.config import get_settings
    from app.db.session import get_session

    rng = np.random.default_rng(get_settings().seed)
    while True:
        async with get_session() as session:
            changed = await run_simulator_tick(session, rng)
            print(f"[simulator] {changed} provider(s) changed state", flush=True)
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_simulator_loop())
