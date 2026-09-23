"""add vat_identifier to companies

Revision ID: e7f4a1c2b9d0
Revises: d4e7b2c1a9f0
Create Date: 2026-09-23
"""

import sqlalchemy as sa
from alembic import op

revision = "e7f4a1c2b9d0"
down_revision = "d4e7b2c1a9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("vat_identifier", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "vat_identifier")
