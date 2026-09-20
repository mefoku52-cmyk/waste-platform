"""add recommendation fields to listings and companies"""

import sqlalchemy as sa
from alembic import op

revision = "d4e7b2c1a9f0"
down_revision = "b9c4d2e8f1a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("listings", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("listings", sa.Column("legal_regime", sa.String(length=32), nullable=True))
    op.add_column("companies", sa.Column("accepted_material_types", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "accepted_material_types")
    op.drop_column("listings", "legal_regime")
    op.drop_column("listings", "longitude")
    op.drop_column("listings", "latitude")
