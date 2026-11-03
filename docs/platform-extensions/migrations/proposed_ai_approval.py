"""Proposed Alembic migration for AI approval requests.

DO NOT place in migrations/versions/. Design proposal only.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "proposed_ai_approval_001"
down_revision = None


def upgrade():
    op.create_table(
        "ai_approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("arguments", postgresql.JSONB, nullable=False),
        sa.Column("arguments_hash", sa.String(64), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolver_id", postgresql.UUID(as_uuid=True)),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
        sa.Column("execution_error", sa.Text),
    )


def downgrade():
    op.drop_table("ai_approval_requests")