import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProviderStateHistory(Base):
    """Append-only log of availability transitions. Current state = latest row per provider_id.

    changed_at uses a Python-side (not server-side) default: SQLite's CURRENT_TIMESTAMP
    only has 1-second resolution, so rapid successive commits for the same provider can
    get identical server_default=func.now() values and make "latest row" ordering
    ambiguous. datetime.now(UTC) has microsecond resolution and is set per-row in the
    application, avoiding that collision on every backend, not just Postgres.
    """

    __tablename__ = "provider_state_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("providers.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
