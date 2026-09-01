"""add provider service areas field

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-11

Added service_areas field to allow providers to select multiple service areas.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("providers", sa.Column("service_areas", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("providers", "service_areas")
