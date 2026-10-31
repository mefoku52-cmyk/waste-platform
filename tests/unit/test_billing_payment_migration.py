from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest


def _migration_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "aa71c2f19d44_add_billing_payment_orders.py"
    )
    spec = spec_from_file_location("billing_payment_migration", path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_payment_migration_reupgrade_and_downgrade_preserve_business_data():
    migration = _migration_module()
    engine = sa.create_engine("sqlite:///:memory:")
    company_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    order_id = uuid4().hex
    event_row_id = uuid4().hex

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE companies (id VARCHAR(36) PRIMARY KEY)"
        )
        connection.execute(
            sa.text("INSERT INTO companies (id) VALUES (:id)"), {"id": company_id}
        )
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            connection.execute(
                sa.text(
                    "INSERT INTO billing_payment_orders "
                    "(id, order_ref, provider, provider_ref, user_id, company_id, "
                    "product_kind, tier, amount_cents, currency, status, stripe_subscription_id) "
                    "VALUES (:id, :order_ref, :provider, :provider_ref, :user_id, :company_id, "
                    ":product_kind, :tier, :amount, :currency, :status, :subscription_id)"
                ),
                {
                    "id": order_id,
                    "order_ref": "order-local-1",
                    "provider": "stripe",
                    "provider_ref": "cs_local_1",
                    "user_id": "user-local-1",
                    "company_id": company_id,
                    "product_kind": "subscription",
                    "tier": "ai",
                    "amount": 2900,
                    "currency": "EUR",
                    "status": "applied",
                    "subscription_id": "sub_local_1",
                },
            )
            connection.execute(
                sa.text(
                    "INSERT INTO billing_webhook_events (id, provider, event_id, event_type) "
                    "VALUES (:id, :provider, :event_id, :event_type)"
                ),
                {
                    "id": event_row_id,
                    "provider": "stripe",
                    "event_id": "evt_local_1",
                    "event_type": "checkout.session.completed",
                },
            )
            with pytest.raises(sa.exc.IntegrityError):
                with connection.begin_nested():
                    connection.execute(
                        sa.text(
                            "INSERT INTO billing_webhook_events "
                            "(id, provider, event_id, event_type) "
                            "VALUES (:id, :provider, :event_id, :event_type)"
                        ),
                        {
                            "id": uuid4().hex,
                            "provider": "stripe",
                            "event_id": "evt_local_1",
                            "event_type": "customer.subscription.updated",
                        },
                    )
            connection.execute(
                sa.text(
                    "UPDATE companies SET stripe_subscription_id=:subscription_id WHERE id=:id"
                ),
                {"subscription_id": "sub_local_1", "id": company_id},
            )

            migration.downgrade()
            assert connection.execute(
                sa.text("SELECT COUNT(*) FROM billing_payment_orders")
            ).scalar_one() == 1
            assert connection.execute(
                sa.text("SELECT COUNT(*) FROM billing_webhook_events")
            ).scalar_one() == 1
            assert connection.execute(
                sa.text("SELECT stripe_subscription_id FROM companies WHERE id=:id"),
                {"id": company_id},
            ).scalar_one() == "sub_local_1"

            # Re-running upgrade after the data-preserving downgrade is safe.
            migration.upgrade()
            assert connection.execute(
                sa.text("SELECT event_id FROM billing_webhook_events WHERE id=:id"),
                {"id": event_row_id},
            ).scalar_one() == "evt_local_1"
            assert "stripe_last_event_created" in {
                column["name"]
                for column in sa.inspect(connection).get_columns("billing_payment_orders")
            }

    engine.dispose()
