"""add ai_conversations and ai_messages

Revision ID: a2b3c4d5e6f7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "a2b3c4d5e6f7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = set(inspector.get_table_names())

    if "ai_conversations" not in tables:
        op.create_table(
            "ai_conversations",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("session_id", sa.String(length=64), nullable=False),
            sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("company_id", sa.UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index(
            "ix_ai_conversations_session_id",
            "ai_conversations",
            ["session_id"],
            unique=True,
        )
        op.create_index(
            "ix_ai_conversations_user_id",
            "ai_conversations",
            ["user_id"],
        )
        op.create_index(
            "ix_ai_conversations_company_id",
            "ai_conversations",
            ["company_id"],
        )

    if "ai_messages" not in tables:
        op.create_table(
            "ai_messages",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "conversation_id",
                sa.UUID(as_uuid=True),
                sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role", sa.String(length=16), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("tool_calls", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index(
            "ix_ai_messages_conversation_id",
            "ai_messages",
            ["conversation_id"],
        )
        op.create_index(
            "ix_ai_messages_conv_created",
            "ai_messages",
            ["conversation_id", "created_at"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = set(inspector.get_table_names())
    if "ai_messages" in tables:
        op.drop_table("ai_messages")
    if "ai_conversations" in tables:
        op.drop_table("ai_conversations")
