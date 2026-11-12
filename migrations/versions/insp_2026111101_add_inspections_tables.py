"""add inspections tables

Revision ID: insp_2026111101
Revises: mcp_phase4plus_20261104
Create Date: 2026-11-11

Zive obhliadky (CMEP Streaming integration):
  inspections         — obhliadka viazana na listing + dve strany
  inspection_events   — eventy zo streamingu (idempotentne podla event_uid)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "insp_2026111101"
down_revision: str | Sequence[str] | None = "mcp_phase4plus_20261104"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inspections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("owner_company_id", sa.UUID(), nullable=False),
        sa.Column("viewer_user_id", sa.UUID(), nullable=True),
        sa.Column("viewer_company_id", sa.UUID(), nullable=True),
        sa.Column("viewer_thread_id", sa.UUID(), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("consent_to_record", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("recording_consent_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column("updated_by_user_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inspections_listing_id", "inspections", ["listing_id"])
    op.create_index("ix_inspections_room_id", "inspections", ["room_id"])
    op.create_index("ix_inspections_owner_user_id", "inspections", ["owner_user_id"])
    op.create_index("ix_inspections_owner_company_id", "inspections", ["owner_company_id"])

    op.create_table(
        "inspection_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_uid", sa.String(length=64), nullable=False),
        sa.Column("inspection_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_uid", name="uq_inspection_events_uid"),
    )
    op.create_index("ix_inspection_events_inspection_id", "inspection_events", ["inspection_id"])
    op.create_index("ix_inspection_events_event_type", "inspection_events", ["event_type"])
    op.create_index("ix_inspection_events_created_at", "inspection_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_inspection_events_created_at", table_name="inspection_events")
    op.drop_index("ix_inspection_events_event_type", table_name="inspection_events")
    op.drop_index("ix_inspection_events_inspection_id", table_name="inspection_events")
    op.drop_table("inspection_events")
    op.drop_index("ix_inspections_owner_company_id", table_name="inspections")
    op.drop_index("ix_inspections_owner_user_id", table_name="inspections")
    op.drop_index("ix_inspections_room_id", table_name="inspections")
    op.drop_index("ix_inspections_listing_id", table_name="inspections")
    op.drop_table("inspections")
