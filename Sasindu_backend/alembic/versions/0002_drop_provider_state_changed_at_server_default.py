"""drop server default on provider_state_history.changed_at

Revision ID: 0002
Revises: 9858a37f948c
Create Date: 2026-07-28

changed_at is now set client-side (datetime.now(UTC), microsecond resolution) on every
insert rather than relying on the database's now() default -- see
app/db/models/provider_state.py for why (SQLite's CURRENT_TIMESTAMP only has 1-second
resolution, which made "latest row = current status" ordering ambiguous under rapid
successive writes). The ORM always supplies changed_at explicitly now, so the stale
DB-level default is removed to keep schema and model in sync.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "9858a37f948c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("provider_state_history", "changed_at", server_default=None)


def downgrade() -> None:
    op.alter_column("provider_state_history", "changed_at", server_default=sa.text("now()"))
