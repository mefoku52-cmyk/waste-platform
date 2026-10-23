"""add listing_type and make quantity nullable for transport

Revision ID: add_listing_type_20261024013009
Revises: e4d5f6a7b8c9
Create Date: 2026-10-24T01:30:09.669004

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_listing_type_20261024013009"
down_revision = "e4d5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pridáme stĺpec listing_type (material / transport)
    op.add_column(
        "listings",
        sa.Column("listing_type", sa.String(length=32), nullable=False, server_default="material"),
    )

    # Povolíme quantity ako nullable (pre dopravu nemusí byť)
    op.alter_column("listings", "quantity", existing_type=sa.Float(), nullable=True)

    # Povolíme unit ako nullable (pre dopravu nemusí byť)
    op.alter_column("listings", "unit", existing_type=sa.String(length=32), nullable=True)

    # Povolíme condition ako nullable (pre dopravu nemusí byť)
    op.alter_column("listings", "condition", existing_type=sa.String(length=120), nullable=True)


def downgrade() -> None:
    op.alter_column("listings", "condition", existing_type=sa.String(length=120), nullable=False)
    op.alter_column("listings", "unit", existing_type=sa.String(length=32), nullable=False)
    op.alter_column("listings", "quantity", existing_type=sa.Float(), nullable=False)
    op.drop_column("listings", "listing_type")
