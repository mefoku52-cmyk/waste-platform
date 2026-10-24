"""add hazardous_types to transport_offers

Revision ID: add_hazardous_01
Revises: transport_offers_01
Create Date: 2026-10-24

"""

import sqlalchemy as sa
from alembic import op

revision = "add_hazardous_01"
down_revision = "transport_offers_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transport_offers", sa.Column("hazardous_types", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("transport_offers", "hazardous_types")
