"""add_listing_views

Revision ID: a8f3c9d1e5b7
Revises: 1577dceccd9e
Create Date: 2026-09-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8f3c9d1e5b7"
down_revision: str | Sequence[str] | None = "1577dceccd9e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgresql() -> bool:
    """CI a lokalne testy bezia na SQLite, produkcia na Postgres.

    `CREATE EXTENSION`, `gen_random_uuid()` a `NOW()` su Postgres-only DDL,
    takze sa aplikuju vyhradne na PostgreSQL. Na ostatnych dialektoch sa
    spolieha na Python-side defaulty modelu (`uuid.uuid4`, `datetime.now`).
    """
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    is_postgres = _is_postgresql()

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    id_column = sa.Column(
        "id",
        sa.UUID(),
        nullable=False,
        server_default=sa.text("gen_random_uuid()") if is_postgres else None,
    )
    viewed_at_column = sa.Column(
        "viewed_at",
        sa.DateTime(),
        nullable=False,
        server_default=sa.text("NOW()") if is_postgres else None,
    )

    op.create_table(
        "listing_views",
        id_column,
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        viewed_at_column,
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listing_views_listing_id", "listing_views", ["listing_id"])
    op.create_index("ix_listing_views_listing_user", "listing_views", ["listing_id", "user_id"])


def downgrade() -> None:
    op.drop_index("ix_listing_views_listing_user", table_name="listing_views")
    op.drop_index("ix_listing_views_listing_id", table_name="listing_views")
    op.drop_table("listing_views")
