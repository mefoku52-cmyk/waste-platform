"""add outreach_candidates table

Revision ID: a3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "a3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = set(inspector.get_table_names())

    if "outreach_candidates" not in tables:
        op.create_table(
            "outreach_candidates",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("company_name", sa.String(length=255), nullable=False),
            sa.Column("ico", sa.String(length=32), nullable=True),
            sa.Column("city", sa.String(length=128), nullable=True),
            sa.Column("industry", sa.String(length=128), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
            sa.Column("draft_subject", sa.String(length=255), nullable=True),
            sa.Column("draft_body", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("sent_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_outreach_candidates_ico", "outreach_candidates", ["ico"])
        op.create_index("ix_outreach_candidates_city", "outreach_candidates", ["city"])
        op.create_index("ix_outreach_candidates_industry", "outreach_candidates", ["industry"])
        op.create_index("ix_outreach_candidates_email", "outreach_candidates", ["email"])
        op.create_index("ix_outreach_candidates_status", "outreach_candidates", ["status"])
        op.create_index(
            "ix_outreach_candidates_city_status",
            "outreach_candidates",
            ["city", "status"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = set(inspector.get_table_names())
    if "outreach_candidates" in tables:
        op.drop_table("outreach_candidates")
