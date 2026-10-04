"""add outreach candidate contact fields

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-10-04

Prida stlpce phone, website, source_url do outreach_candidates.
Dovod: ZS category discovery ich extrahuje z kariet, ale model ich
zatial nemal — hodnoty sa zahadzovali a logovali ako WARNING.

Idempotentne: pred kazdym add_column skontrolujeme, ci stlpec uz
existuje (bezpecne pre pripad ciastocne aplikovanej migracie).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "c6d7e8f9a0b1"
down_revision = "b5c6d7e8f9a0"
branch_labels = None
depends_on = None


def _existing_columns(conn, table: str) -> set[str]:
    inspector = inspect(conn)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()
    existing = _existing_columns(conn, "outreach_candidates")

    if "phone" not in existing:
        op.add_column(
            "outreach_candidates",
            sa.Column("phone", sa.String(length=64), nullable=True),
        )

    if "website" not in existing:
        op.add_column(
            "outreach_candidates",
            sa.Column("website", sa.String(length=512), nullable=True),
        )

    if "source_url" not in existing:
        op.add_column(
            "outreach_candidates",
            sa.Column("source_url", sa.String(length=512), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    existing = _existing_columns(conn, "outreach_candidates")

    if "source_url" in existing:
        op.drop_column("outreach_candidates", "source_url")

    if "website" in existing:
        op.drop_column("outreach_candidates", "website")

    if "phone" in existing:
        op.drop_column("outreach_candidates", "phone")
