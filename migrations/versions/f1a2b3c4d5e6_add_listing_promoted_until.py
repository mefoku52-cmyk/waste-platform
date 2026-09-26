"""add promoted_until and promoted_tier to listings

Revision ID: f1a2b3c4d5e6
Revises: e7f4a1c2b9d0
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "f1a2b3c4d5e6"
down_revision = "e7f4a1c2b9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("listings")]
    if "promoted_until" not in columns:
        op.add_column(
            "listings",
            sa.Column("promoted_until", sa.DateTime(timezone=True), nullable=True),
        )
    if "promoted_tier" not in columns:
        op.add_column(
            "listings",
            sa.Column("promoted_tier", sa.String(length=16), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("listings")]
    if "promoted_tier" in columns:
        op.drop_column("listings", "promoted_tier")
    if "promoted_until" in columns:
        op.drop_column("listings", "promoted_until")
