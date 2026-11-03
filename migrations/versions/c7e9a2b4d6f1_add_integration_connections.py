"""Create integration connections table."""

import sqlalchemy as sa
from alembic import op

revision = "c7e9a2b4d6f1"
down_revision = "aa71c2f19d44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_connections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("integration_type", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("encrypted_credentials", sa.Text(), nullable=True),
        sa.Column(
            "last_sync_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_integration_connections_company_id",
        "integration_connections",
        ["company_id"],
        unique=False,
    )

    op.create_index(
        "ix_integration_connections_integration_type",
        "integration_connections",
        ["integration_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_integration_connections_integration_type",
        table_name="integration_connections",
    )
    op.drop_index(
        "ix_integration_connections_company_id",
        table_name="integration_connections",
    )
    op.drop_table("integration_connections")
