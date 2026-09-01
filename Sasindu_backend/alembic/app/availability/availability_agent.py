import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.provider_state import ProviderStateHistory


@dataclass
class AvailabilityInfo:
    status: str
    acceptance_probability: float


class AvailabilityAgent:
    async def filter_and_score(self, session: AsyncSession, provider_ids: list[str]) -> dict[str, AvailabilityInfo]:
        results: dict[str, AvailabilityInfo] = {}
        for provider_id in provider_ids:
            stmt = (
                select(ProviderStateHistory.status)
                .where(ProviderStateHistory.provider_id == uuid.UUID(provider_id))
                .order_by(ProviderStateHistory.changed_at.desc())
                .limit(10)
            )
            rows = (await session.execute(stmt)).scalars().all()
            # No history yet (e.g. the simulator hasn't ticked for this provider) --
            # the simulator itself defaults an unseen provider's implicit state to
            # "online" (see simulator.py's _current_state), so match that here rather
            # than silently excluding every provider before the simulator's first tick.
            if not rows:
                rows = ["online"]
            current_status = rows[0]
            if current_status == "offline":
                continue

            online_fraction = sum(1 for s in rows if s == "online") / len(rows)
            acceptance_probability = (online_fraction * len(rows) + 0.5) / (len(rows) + 1)

            results[provider_id] = AvailabilityInfo(
                status=current_status, acceptance_probability=round(acceptance_probability, 4)
            )
        return results
