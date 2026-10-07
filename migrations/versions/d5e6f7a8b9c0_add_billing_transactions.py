"""add billing_transactions

Revision ID: d5e6f7a8b9c0
Revises: c7d8e9f0a1b2
Create Date: 2026-10-08
"""

import sqlalchemy as sa
from alembic import op

revision = "d5e6f7a8b9c0"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_transactions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False, server_default="pro"),
        sa.Column("order_number", sa.String(length=32), nullable=False, unique=True),
        sa.Column("payment_id", sa.BigInteger(), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="CREATED"),
        sa.Column("gw_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_billing_tx_company", "billing_transactions", ["company_id"])
    op.create_index("ix_billing_tx_order", "billing_transactions", ["order_number"], unique=True)


def downgrade() -> None:
    op.drop_table("billing_transactions")
