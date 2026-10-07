"""add logo_url to companies

Revision ID: c7d8e9f0a1b2
Revises: ab3fa1390046
Create Date: 2026-10-07

"""

import sqlalchemy as sa
from alembic import op

revision = "c7d8e9f0a1b2"
down_revision = "ab3fa1390046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("logo_url", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "logo_url")
