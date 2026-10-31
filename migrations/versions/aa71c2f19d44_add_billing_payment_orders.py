"""add unified billing payment orders and webhook event receipts

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


_ORDER_COLUMNS = {
    "id",
    "order_ref",
    "provider",
    "provider_ref",
    "user_id",
    "company_id",
    "listing_id",
    "product_kind",
    "tier",
    "duration_days",
    "amount_cents",
    "currency",
    "status",
    "stripe_subscription_id",
    "created_at",
    "processed_at",
}
_EVENT_COLUMNS = {"id", "provider", "event_id", "event_type", "received_at"}


def _inspector():
    return sa.inspect(op.get_bind())


def _require_columns(table: str, expected: set[str]) -> None:
    existing = {column["name"] for column in _inspector().get_columns(table)}
    missing = expected - existing
    if missing:
        raise RuntimeError(
            f"Existing {table} table has an incompatible schema; missing columns: "
            + ", ".join(sorted(missing))
        )


def _ensure_index(table: str, name: str, columns: list[str]) -> None:
    indexes = {index["name"]: index.get("column_names") for index in _inspector().get_indexes(table)}
    if name in indexes:
        if indexes[name] != columns:
            raise RuntimeError(f"Existing index {name} has unexpected columns")
        return
    op.create_index(name, table, columns)


def _ensure_payment_orders() -> None:
    inspector = _inspector()
    if not inspector.has_table("billing_payment_orders"):
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
    else:
        _require_columns("billing_payment_orders", _ORDER_COLUMNS)

    if "stripe_last_event_created" not in {c["name"] for c in _inspector().get_columns("billing_payment_orders")}:
        op.add_column(
            "billing_payment_orders",
            sa.Column("stripe_last_event_created", sa.Integer(), nullable=True),
        )
    _ensure_index("billing_payment_orders", "ix_billing_payment_orders_company_id", ["company_id"])
    _ensure_index("billing_payment_orders", "ix_billing_payment_orders_status", ["status"])
    _ensure_index(
        "billing_payment_orders",
        "ix_billing_payment_orders_stripe_subscription_id",
        ["stripe_subscription_id"],
    )


def _ensure_webhook_events() -> None:
    inspector = _inspector()
    if not inspector.has_table("billing_webhook_events"):
        op.create_table(
            "billing_webhook_events",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("provider", sa.String(length=16), nullable=False),
            sa.Column("event_id", sa.String(length=128), nullable=False),
            sa.Column("event_type", sa.String(length=128), nullable=False),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "provider", "event_id", name="uq_billing_webhook_events_provider_event"
            ),
        )
    else:
        _require_columns("billing_webhook_events", _EVENT_COLUMNS)
        constraints = _inspector().get_unique_constraints("billing_webhook_events")
        if not any(c.get("column_names") == ["provider", "event_id"] for c in constraints):
            raise RuntimeError(
                "Existing billing_webhook_events table lacks unique (provider, event_id) constraint"
            )


def upgrade() -> None:
    _ensure_payment_orders()
    _ensure_webhook_events()

    inspector = _inspector()
    if not inspector.has_table("companies"):
        raise RuntimeError("Required companies table is missing")
    company_columns = {c["name"] for c in inspector.get_columns("companies")}
    if "stripe_subscription_id" not in company_columns:
        op.add_column("companies", sa.Column("stripe_subscription_id", sa.String(length=128), nullable=True))


def downgrade() -> None:
    # Intentionally forward-only: billing orders, signed webhook receipts, and
    # active subscription IDs are business/audit data. Dropping these objects
    # would lose payment evidence and break reconciliation. Older app versions
    # may safely ignore the extra schema; re-upgrade is idempotent.
    pass
