"""add unified billing payment orders

Revision ID: aa71c2f19d44
Revises: add_hazardous_01
Create Date: 2026-10-31
"""

import sqlalchemy as sa
from alembic import op

revision = "aa71c2f19d44"
down_revision = "add_hazardous_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_payment_orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_ref", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=16), nullable=False),
        sa.Column("provider_ref", sa.String(length=128), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.String(length=36), nullable=True),
        sa.Column("product_kind", sa.String(length=24), nullable=False),
        sa.Column("tier", sa.String(length=24), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("stripe_subscription_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_ref"),
        sa.UniqueConstraint("provider_ref"),
    )
    op.create_index("ix_billing_payment_orders_company_id", "billing_payment_orders", ["company_id"])
    op.create_index("ix_billing_payment_orders_status", "billing_payment_orders", ["status"])
    op.create_index(
        "ix_billing_payment_orders_subscription_id",
        "billing_payment_orders",
        ["stripe_subscription_id"],
    )
    op.add_column("companies", sa.Column("stripe_subscription_id", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "stripe_subscription_id")
    op.drop_index("ix_billing_payment_orders_subscription_id", table_name="billing_payment_orders")
    op.drop_index("ix_billing_payment_orders_status", table_name="billing_payment_orders")
    op.drop_index("ix_billing_payment_orders_company_id", table_name="billing_payment_orders")
    op.drop_table("billing_payment_orders")
