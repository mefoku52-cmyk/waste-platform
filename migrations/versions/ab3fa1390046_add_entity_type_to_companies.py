"""add entity_type to companies

Revision ID: ab3fa1390046
Revises: c6d7e8f9a0b1
Create Date: 2026-10-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "ab3fa1390046"
down_revision = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("companies")]
    if "entity_type" not in columns:
        op.add_column(
            "companies",
            sa.Column(
                "entity_type",
                sa.String(length=32),
                nullable=False,
                server_default="company",
            ),
        )
        op.create_index(
            "ix_companies_entity_type",
            "companies",
            ["entity_type"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("companies")]
    if "entity_type" in columns:
        op.drop_index("ix_companies_entity_type", table_name="companies")
        op.drop_column("companies", "entity_type")
