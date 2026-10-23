"""create transport_offers table

Revision ID: transport_offers_01
Revises: add_listing_type_20261024013009
Create Date: 2026-10-24T01:34:37.379513

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "transport_offers_01"
down_revision = "add_listing_type_20261024013009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transport_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transport_from", sa.String(length=255), nullable=False),
        sa.Column("transport_to", sa.String(length=255), nullable=True),
        sa.Column("vehicle_type", sa.String(length=120), nullable=False),
        sa.Column("capacity_tons", sa.Float(), nullable=True),
        sa.Column("price_per_km", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="EUR"),
        sa.Column("has_refrigeration", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_adr", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_hydraulic_arm", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("transport_offers")
