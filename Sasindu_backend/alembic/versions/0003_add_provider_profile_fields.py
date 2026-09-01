"""add provider profile fields (phone, years_experience, avatar_url)

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-29

Added nullable at the DB level (rather than NOT NULL, which would fail against the
150 existing rows with no value to backfill) -- the seed script always supplies all
three on every row it creates, so re-seeding after this migration fills them in.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("providers", sa.Column("phone", sa.String(length=30), nullable=True))
    op.add_column("providers", sa.Column("years_experience", sa.Integer(), nullable=True))
    op.add_column("providers", sa.Column("avatar_url", sa.String(length=300), nullable=True))


def downgrade() -> None:
    op.drop_column("providers", "avatar_url")
    op.drop_column("providers", "years_experience")
    op.drop_column("providers", "phone")
