"""Tests for the Stripe billing endpoints (hermetic — Stripe SDK is mocked).

No network calls: `stripe.checkout.Session.create` and `stripe.Webhook.construct_event`
are monkeypatched. Covers:
- checkout requires configured STRIPE_SECRET_KEY
- checkout rejects unknown tier/days and promote without listing_id
- checkout builds correct metadata
- webhook rejects unconfigured Stripe
- webhook rejects invalid signature
- webhook promotes the listing on checkout.session.completed
- webhook ignores non-checkout events
"""

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import stripe
from fastapi.testclient import TestClient

from app.main import app
from app.modules.billing.infrastructure.models import (
    BillingPaymentOrderModel,
    BillingWebhookEventModel,
)
from app.modules.companies.infrastructure.models import CompanyModel
from app.modules.listings.infrastructure.models import ListingsModel
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user

COMPANY_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LISTING_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
USER_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


class _FakeUser:
    def __init__(self):
        self.id = USER_ID
        self.email = "test@example.com"
        self.isPlatformAdmin = False
        self.memberships = [SimpleNamespace(companyId=COMPANY_ID, membershipRole="owner")]


class _FakeResult:
    def __init__(self, value=None, rowcount=0):
        self.value = value
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self.value


class _FakeDbSession:
    def __init__(self):
        self.order = None
        self.listing = SimpleNamespace(
            id=UUID(LISTING_ID), company_id=UUID(COMPANY_ID),
            promoted_until=None, promoted_tier=None,
        )
        self.company = SimpleNamespace(id=COMPANY_ID, stripe_subscription_id=None, subscription_tier="free")
        self.webhook_events = {}

    async def get(self, model, key):
        if model is ListingsModel and str(key) == LISTING_ID:
            return self.listing
        if model is CompanyModel and str(key) == COMPANY_ID:
            return self.company
        if model is BillingPaymentOrderModel and self.order is not None:
            return self.order if key == getattr(self.order, "id", None) else None
        return None

    def add(self, value):
        if isinstance(value, BillingPaymentOrderModel):
            self.order = value
        elif isinstance(value, BillingWebhookEventModel):
            self.webhook_events[value.event_id] = value

    async def flush(self):
        return None

    async def execute(self, statement, *args, **kwargs):
        if getattr(statement, "is_update", False):
            self.company.subscription_tier = "free"
            values = getattr(statement, "_values", {})
            value_names = {getattr(column, "key", str(column)) for column in values}
            if "stripe_subscription_id" in value_names:
                self.company.stripe_subscription_id = None
            return _FakeResult(rowcount=1)
        descriptions = getattr(statement, "column_descriptions", [])
        if descriptions and descriptions[0].get("entity") is BillingWebhookEventModel:
            params = statement.compile().params
            event_id = next(
                (value for key, value in params.items() if "event_id" in key), None
            )
            return _FakeResult(self.webhook_events.get(str(event_id)))
        if descriptions and descriptions[0].get("entity") is CompanyModel:
            params = statement.compile().params
            for key, value in params.items():
                if key.startswith("id_") and str(self.company.id) != str(value):
                    return _FakeResult()
                if key.startswith("stripe_subscription_id_") and str(self.company.stripe_subscription_id) != str(value):
                    return _FakeResult()
            return _FakeResult(self.company)
        if descriptions and descriptions[0].get("entity") is BillingPaymentOrderModel:
            candidate = self.order
            if candidate is None:
                return _FakeResult()
            params = statement.compile().params
            for key, value in params.items():
                if key.startswith("order_ref") and getattr(candidate, "order_ref", None) != value:
                    return _FakeResult()
                if key.startswith("provider_") and getattr(candidate, "provider", None) != value:
                    return _FakeResult()
                if key.startswith("product_kind") and getattr(candidate, "product_kind", None) != value:
                    return _FakeResult()
                if key.startswith("stripe_subscription_id") and getattr(candidate, "stripe_subscription_id", None) != value:
                    return _FakeResult()
                if key.startswith("status_") and getattr(candidate, "status", None) != value:
                    return _FakeResult()
            return _FakeResult(candidate)
        return _FakeResult(self.order)

    async def commit(self):
        return None

    async def rollback(self):
        return None


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def fake_session():
    return _FakeDbSession()


@pytest.fixture(autouse=True)
def _override_auth(fake_session):
    async def _db_session():
        yield fake_session

    app.dependency_overrides[require_current_user] = lambda: _FakeUser()
    app.dependency_overrides[get_db_session] = _db_session
    yield
    app.dependency_overrides.clear()


def _set_stripe_keys(monkeypatch, secret="sk_test_x", webhook="whsec_x"):
    from app.core.config import settings

    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", secret, raising=False)
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", webhook, raising=False)


def _unset_stripe_keys(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", None, raising=False)
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", None, raising=False)


def _set_gopay_config(monkeypatch, amount=5000):
    from app.core.config import settings
    from app.modules.billing.presentation import router as billing_router

    cfg = {
        "client_id": "client",
        "client_secret": "secret",
        "goid": "1234567890",
        "api": "https://gw.sandbox.gopay.com",
        "return_url": "https://trc-cmep.sk/payment/return",
        "notify_url": "https://trc-cmep.sk/api/v1/billing/notify",
    }
    monkeypatch.setattr(billing_router, "_cfg", lambda: cfg)
    monkeypatch.setitem(settings.__dict__, "GOPAY_PRO_AMOUNT_CENTS", amount)


def _checkout_body(**over):
    body = {
        "kind": "promote",
        "listing_id": LISTING_ID,
        "days": 7,
        "tier": "top",
        "success_url": "https://trc-cmep.sk/success",
        "cancel_url": "https://trc-cmep.sk/cancel",
    }
    body.update(over)
    return body


def test_checkout_503_when_stripe_not_configured(client, monkeypatch):
    _unset_stripe_keys(monkeypatch)
    r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())
    assert r.status_code == 503


def test_checkout_rejects_unknown_tier(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    with patch("stripe.checkout.Session.create") as create:
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body(tier="platinum"))
        create.assert_not_called()
    assert r.status_code == 422


def test_checkout_promote_requires_listing_id(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    with patch("stripe.checkout.Session.create") as create:
        r = client.post(
            "/api/v1/billing/stripe/checkout",
            json=_checkout_body(listing_id=None),
        )
        create.assert_not_called()
    assert r.status_code == 422


def test_checkout_creates_session_with_metadata(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    fake = MagicMock()
    fake.url = "https://checkout.stripe.com/c/pay_123"
    fake.id = "cs_123"
    with patch("stripe.checkout.Session.create", return_value=fake) as create:
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["url"] == "https://checkout.stripe.com/c/pay_123"
    md = create.call_args.kwargs["metadata"]
    assert md["kind"] == "promote"
    assert md["listing_id"] == LISTING_ID
    assert md["company_id"] == COMPANY_ID
    assert md["user_id"] == USER_ID
    assert md["order_ref"]
    assert md["days"] == "7"
    assert md["tier"] == "top"


def test_webhook_503_when_not_configured(client, monkeypatch):
    _unset_stripe_keys(monkeypatch)
    r = client.post(
        "/api/v1/billing/stripe/webhook",
        content=b"{}",
        headers={"stripe-signature": "x"},
    )
    assert r.status_code == 503


def test_webhook_rejects_bad_signature(client, monkeypatch):
    _set_stripe_keys(monkeypatch)

    import stripe

    def _boom(payload, sig, secret):
        raise stripe.error.SignatureVerificationError("bad", sig_header=sig)

    with patch("stripe.Webhook.construct_event", side_effect=_boom):
        r = client.post(
            "/api/v1/billing/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "bad"},
        )

    assert r.status_code == 400
    assert "Invalid signature" in r.text


def _promotion_order(**overrides):
    values = {
        "id": uuid4(), "order_ref": "order-123", "provider": "stripe",
        "provider_ref": "cs_123", "user_id": USER_ID, "company_id": COMPANY_ID,
        "listing_id": LISTING_ID, "product_kind": "promotion", "tier": "gold",
        "duration_days": 30, "amount_cents": 3000, "currency": "EUR", "status": "pending",
        "stripe_subscription_id": None, "processed_at": None,
    }
    values.update(overrides)
    return BillingPaymentOrderModel(**values)


def _promotion_event():
    return {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_123", "mode": "payment", "payment_status": "paid",
            "amount_total": 3000, "currency": "eur",
            "metadata": {
                "kind": "promote", "order_ref": "order-123", "listing_id": LISTING_ID,
                "company_id": COMPANY_ID, "user_id": USER_ID, "days": "30", "tier": "gold",
            },
        }},
    }


def test_webhook_promotes_listing_once_and_validates_server_order(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    fake_session.order = _promotion_order()
    with patch("stripe.Webhook.construct_event", return_value=_promotion_event()):
        r = client.post("/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"})
    assert r.status_code == 200, r.text
    assert fake_session.order.status == "applied"
    assert fake_session.listing.promoted_tier == "gold"
    first_until = fake_session.listing.promoted_until

    # A duplicate provider event must not grant the same paid period twice.
    with patch("stripe.Webhook.construct_event", return_value=_promotion_event()):
        duplicate = client.post("/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"})
    assert duplicate.status_code == 200, duplicate.text
    assert fake_session.listing.promoted_until == first_until


def test_webhook_rejects_mismatched_payment_amount(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    fake_session.order = _promotion_order()
    event = _promotion_event()
    event["data"]["object"]["amount_total"] = 1
    with patch("stripe.Webhook.construct_event", return_value=event):
        r = client.post("/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"})
    assert r.status_code == 400
    assert fake_session.order.status == "pending"


def test_webhook_other_event_types_are_ignored(client, monkeypatch):
    _set_stripe_keys(monkeypatch)

    with patch(
        "stripe.Webhook.construct_event",
        return_value={"type": "payment_intent.succeeded", "data": {"object": {}}},
    ):
        r = client.post(
            "/api/v1/billing/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "ok"},
        )

    assert r.status_code == 200
    assert r.json() == {"received": True}


def test_webhook_rejects_invalid_payload(client, monkeypatch):
    _set_stripe_keys(monkeypatch)

    with patch("stripe.Webhook.construct_event", side_effect=ValueError("bad payload")):
        r = client.post(
            "/api/v1/billing/stripe/webhook",
            content=b"not-json",
            headers={"stripe-signature": "ok"},
        )

    assert r.status_code == 400
    assert "Invalid payload" in r.text


def test_webhook_skips_promote_when_no_listing_id(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    with patch(
        "stripe.Webhook.construct_event",
        return_value={
            "id": "evt_missing_order_ref",
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"kind": "promote", "days": "7", "tier": "top"}}},
        },
    ):
        r = client.post(
            "/api/v1/billing/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "ok"},
        )

    assert r.status_code == 200


def test_webhook_skips_promote_when_kind_not_promote(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    with patch(
        "stripe.Webhook.construct_event",
        return_value={
            "id": "evt_untracked_kind",
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"kind": "donation", "listing_id": "list-9"}}},
        },
    ):
        r = client.post(
            "/api/v1/billing/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "ok"},
        )

    assert r.status_code == 200


def test_webhook_ignores_untracked_legacy_checkout_without_granting_promotion(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    with patch("stripe.Webhook.construct_event", return_value=_promotion_event()):
        r = client.post("/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"})
    assert r.status_code == 200
    assert fake_session.listing.promoted_tier is None


def test_checkout_rejects_unapproved_return_origin(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    with patch("stripe.checkout.Session.create") as create:
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body(success_url="https://evil.example/steal"))
    assert r.status_code == 422
    create.assert_not_called()


def test_checkout_rejects_listing_from_another_company(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(
        id=USER_ID, email="test@example.com", isPlatformAdmin=False, memberships=[]
    )
    with patch("stripe.checkout.Session.create") as create:
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())
    assert r.status_code == 403
    create.assert_not_called()


def test_subscription_checkout_is_recurring_and_company_admin_scoped(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    fake = MagicMock(url="https://checkout.stripe.com/c/sub", id="cs_sub")
    body = {
        "tier": "ai_navigation", "company_id": COMPANY_ID,
        "success_url": "https://trc-cmep.sk/dashboard/subscription?success=true",
        "cancel_url": "https://trc-cmep.sk/dashboard/subscription?cancelled=true",
    }
    with patch("stripe.checkout.Session.create", return_value=fake) as create:
        r = client.post("/api/v1/billing/stripe/subscription", json=body)
    assert r.status_code == 200, r.text
    args = create.call_args.kwargs
    assert args["mode"] == "subscription"
    assert args["line_items"][0]["price_data"]["recurring"] == {"interval": "month"}
    assert args["line_items"][0]["price_data"]["unit_amount"] == 9900
    assert args["metadata"]["tier"] == "ai_navigation"
    assert args["subscription_data"]["metadata"]["order_ref"] == fake_session.order.order_ref


def test_subscription_webhook_grants_exact_tier_and_records_subscription(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    fake_session.order = BillingPaymentOrderModel(
        id=uuid4(), order_ref="sub-order", provider="stripe", provider_ref="cs_sub",
        user_id=USER_ID, company_id=COMPANY_ID, product_kind="subscription",
        tier="ai_navigation", amount_cents=9900, currency="EUR", status="pending",
    )
    event = {
        "id": "evt_sub_checkout",
        "type": "checkout.session.completed",
        "created": 100,
        "data": {"object": {
            "id": "cs_sub", "mode": "subscription", "payment_status": "paid",
            "amount_total": 9900, "currency": "eur", "subscription": "sub_live_123",
            "metadata": {"kind": "subscription", "order_ref": "sub-order", "tier": "ai_navigation", "company_id": COMPANY_ID, "user_id": USER_ID},
        }},
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        r = client.post("/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"})
    assert r.status_code == 200, r.text
    assert fake_session.order.status == "applied"
    assert fake_session.company.subscription_tier == "ai_navigation"
    assert fake_session.company.stripe_subscription_id == "sub_live_123"


def test_webhook_uses_cancellation_event_to_downgrade_matching_subscription(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    fake_session.company.stripe_subscription_id = "sub_cancelled"
    fake_session.company.subscription_tier = "ai"
    fake_session.order = BillingPaymentOrderModel(
        id=uuid4(), order_ref="cancel-order", provider="stripe", provider_ref="cs_cancel",
        stripe_subscription_id="sub_cancelled", user_id=USER_ID, company_id=COMPANY_ID,
        product_kind="subscription", tier="ai", amount_cents=2900, currency="EUR", status="applied",
    )
    event = {
        "id": "evt_sub_deleted", "type": "customer.subscription.deleted", "created": 200,
        "data": {"object": {"id": "sub_cancelled"}},
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        r = client.post("/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"})
    assert r.status_code == 200
    assert fake_session.company.subscription_tier == "free"
    assert fake_session.company.stripe_subscription_id is None


def test_subscription_status_event_removes_entitlement_without_losing_recovery_link(
    client, monkeypatch, fake_session
):
    _set_stripe_keys(monkeypatch)
    fake_session.company.stripe_subscription_id = "sub_past_due"
    fake_session.company.subscription_tier = "ai"
    fake_session.order = BillingPaymentOrderModel(
        id=uuid4(), order_ref="sub-recovery-order", provider="stripe",
        provider_ref="cs_sub", stripe_subscription_id="sub_past_due",
        user_id=USER_ID, company_id=COMPANY_ID, product_kind="subscription",
        tier="ai", amount_cents=2900, currency="EUR", status="applied",
    )
    event = {
        "id": "evt_sub_unpaid",
        "type": "customer.subscription.updated",
        "created": 300,
        "data": {"object": {"id": "sub_past_due", "status": "unpaid"}},
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        response = client.post(
            "/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"}
        )
    assert response.status_code == 200, response.text
    assert fake_session.company.subscription_tier == "free"
    assert fake_session.company.stripe_subscription_id == "sub_past_due"


# ---------------------------------------------------------------------------
# Checkout pricing, error mapping and safe logging
# ---------------------------------------------------------------------------


def _invalid_request_error(
    message: str, *, code: str = "account_inactive"
) -> stripe.error.StripeError:
    json_body = {"error": {"type": "invalid_request_error", "code": code, "message": message}}
    return stripe.error.InvalidRequestError(message, None, code=code, json_body=json_body)


def _card_error(message: str, *, code: str = "card_declined") -> stripe.error.StripeError:
    json_body = {"error": {"type": "card_error", "code": code, "message": message}}
    return stripe.error.CardError(message, None, code, json_body=json_body)


def test_checkout_top_7_costs_500_cents(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    fake = MagicMock(url="https://checkout.stripe.com/c/pay_x", id="cs_x")
    with patch("stripe.checkout.Session.create", return_value=fake) as create:
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body(days=7, tier="top"))

    assert r.status_code == 200, r.text
    kwargs = create.call_args.kwargs
    assert kwargs["mode"] == "payment"
    line = kwargs["line_items"][0]["price_data"]
    assert line["currency"] == "eur"
    assert line["unit_amount"] == 500


def test_checkout_gold_30_costs_3000_cents(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    fake = MagicMock(url="https://checkout.stripe.com/c/pay_y", id="cs_y")
    with patch("stripe.checkout.Session.create", return_value=fake) as create:
        r = client.post(
            "/api/v1/billing/stripe/checkout", json=_checkout_body(days=30, tier="gold")
        )

    assert r.status_code == 200, r.text
    assert create.call_args.kwargs["line_items"][0]["price_data"]["unit_amount"] == 3000


def test_checkout_invalid_request_returns_400_with_safe_detail(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    with patch(
        "stripe.checkout.Session.create",
        side_effect=_invalid_request_error("Your account cannot currently make live charges."),
    ):
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 400
    assert r.json()["detail"].startswith("Stripe error:")
    assert "cannot currently make live charges" in r.json()["detail"]


def test_checkout_card_error_returns_400(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    with patch(
        "stripe.checkout.Session.create", side_effect=_card_error("Your card was declined.")
    ):
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 400
    assert r.json()["detail"].startswith("Stripe error:")


def test_checkout_auth_error_returns_503_without_leaking_provider_message(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    err = stripe.error.AuthenticationError(
        "Invalid API Key provided: sk_live_ABC123SECRET",
        code="api_key_invalid",
        json_body={"error": {"type": "invalid_request_error", "code": "api_key_invalid"}},
    )
    with patch("stripe.checkout.Session.create", side_effect=err):
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 503
    assert "sk_live_ABC123SECRET" not in r.text


def test_checkout_rate_limit_returns_429(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    err = stripe.error.RateLimitError("Too many requests", code="rate_limit")
    with patch("stripe.checkout.Session.create", side_effect=err):
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 429


def test_checkout_connection_error_returns_502(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    err = stripe.error.APIConnectionError("Network error")
    with patch("stripe.checkout.Session.create", side_effect=err):
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 502


def test_checkout_stripe_error_log_is_structured_and_redacted(client, monkeypatch, caplog):
    _set_stripe_keys(monkeypatch)
    secret_in_message = "key sk_live_SECRETVALUE123 rejected"
    with (
        caplog.at_level(logging.WARNING, logger="app.modules.billing.presentation.router"),
        patch(
            "stripe.checkout.Session.create",
            side_effect=_invalid_request_error(secret_in_message),
        ),
    ):
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 400
    log = caplog.text
    # structured, correlatable fields are present
    assert "stripe.checkout failed" in log
    assert "correlation_id=" in log
    assert "class=InvalidRequestError" in log
    assert "type=invalid_request_error" in log
    assert "code=account_inactive" in log
    # secrets are redacted, never written verbatim
    assert "sk_live_SECRETVALUE123" not in log
    assert "[REDACTED]" in log


def test_redact_helper_strips_all_secret_patterns():
    from app.modules.billing.presentation.router import _redact

    assert "sk_live_" not in _redact("sk_live_ABC123")
    assert "sk_test_" not in _redact("sk_test_ABC123")
    assert "pk_live_" not in _redact("pk_live_ABC123")
    assert "whsec_" not in _redact("whsec_ABC123")
    assert "Bearer abc.def" not in _redact("Authorization: Bearer abc.def")
    assert "[REDACTED]" in _redact("sk_live_ABC123")
    # long messages are truncated
    assert _redact("x" * 1000).endswith("...(truncated)")


def test_checkout_only_uses_params_supported_by_sdk_api_version(client, monkeypatch):
    """Regression (N1): every kwarg passed to Session.create must exist in the
    installed Stripe SDK's param schema for the pinned API version.

    The SDK default API version (2026-09-30.endive) dropped
    ``payment_method_types``; passing it makes Stripe reject the call with HTTP
    400. The card-only intent must instead use ``allowed_payment_method_types``.
    """
    from stripe.params.checkout._session_create_params import SessionCreateParams

    _set_stripe_keys(monkeypatch)
    fake = MagicMock()
    fake.url = "https://checkout.stripe.com/c/pay_123"
    fake.id = "cs_123"
    with patch("stripe.checkout.Session.create", return_value=fake) as create:
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body())

    assert r.status_code == 200, r.text
    kwargs = create.call_args.kwargs
    valid = set(SessionCreateParams.__annotations__.keys())
    unsupported = set(kwargs) - valid
    assert not unsupported, f"unsupported Session.create params: {sorted(unsupported)}"
    # card-only intent preserved through the current API's replacement param
    assert kwargs.get("allowed_payment_method_types") == ["card"]


# ---------------------------------------------------------------------------
# Follow-up security regressions: GoPay binding and Stripe event lifecycle
# ---------------------------------------------------------------------------


def test_gopay_checkout_uses_server_owned_price_and_assigns_order_ref(
    client, monkeypatch, fake_session
):
    from app.modules.billing.presentation import router as billing_router

    _set_gopay_config(monkeypatch, amount=6400)

    class _Response:
        status_code = 200

        @staticmethod
        def json():
            return {"id": 123456, "gw_url": "https://gw.sandbox.gopay.com/pay/123456"}

    class _AsyncClient:
        body = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            self.body = kwargs["json"]
            return _Response()

    fake_http = _AsyncClient()
    payload = {
        "company_id": COMPANY_ID,
        "tier": "pro",
        "amount_cents": 1,
        "currency": "USD",
    }
    with (
        patch.object(billing_router, "_token", new=AsyncMock(return_value="access-token")),
        patch.object(billing_router.httpx, "AsyncClient", return_value=fake_http),
    ):
        response = client.post("/api/v1/billing/checkout", json=payload)

    assert response.status_code == 200, response.text
    assert fake_http.body["amount"] == 6400
    assert fake_http.body["currency"] == "EUR"
    assert fake_http.body["order_number"] == response.json()["order_number"]
    assert fake_session.order.order_ref == response.json()["order_number"]
    assert fake_session.order.tier == "pro"
    assert fake_session.order.amount_cents == 6400


def _gopay_paid_response(**overrides):
    value = {
        "id": "123456",
        "order_number": "gopay-order-1",
        "state": "PAID",
        "amount": 5000,
        "currency": "EUR",
        "target": {"type": "ACCOUNT", "goid": 1234567890},
    }
    value.update(overrides)
    return value


def _gopay_order():
    return BillingPaymentOrderModel(
        id=uuid4(),
        order_ref="gopay-order-1",
        provider="gopay",
        provider_ref="123456",
        user_id=USER_ID,
        company_id=COMPANY_ID,
        product_kind="subscription",
        tier="pro",
        amount_cents=5000,
        currency="EUR",
        status="pending",
    )


def test_gopay_callback_applies_only_matching_verified_order(client, monkeypatch, fake_session):
    from app.modules.billing.presentation import router as billing_router

    _set_gopay_config(monkeypatch)
    fake_session.order = _gopay_order()
    with patch.object(
        billing_router,
        "_payment",
        new=AsyncMock(return_value=_gopay_paid_response()),
    ):
        response = client.get("/api/v1/billing/notify?id=123456")

    assert response.status_code == 200, response.text
    assert fake_session.order.status == "applied"
    assert fake_session.company.subscription_tier == "pro"
    with patch.object(
        billing_router,
        "_payment",
        new=AsyncMock(return_value=_gopay_paid_response()),
    ):
        duplicate = client.get("/api/v1/billing/notify?id=123456")
    assert duplicate.status_code == 200
    assert duplicate.json()["updated"] == 0


def test_gopay_callback_rejects_wrong_merchant_or_conflicting_order(client, monkeypatch, fake_session):
    from app.modules.billing.presentation import router as billing_router

    _set_gopay_config(monkeypatch)
    fake_session.order = _gopay_order()
    wrong_merchant = _gopay_paid_response(target={"type": "ACCOUNT", "goid": 999})
    with patch.object(billing_router, "_payment", new=AsyncMock(return_value=wrong_merchant)):
        response = client.get("/api/v1/billing/notify?id=123456")
    assert response.status_code == 400
    assert fake_session.order.status == "pending"

    conflicting_order = _gopay_paid_response(order_number="another-order")
    with patch.object(billing_router, "_payment", new=AsyncMock(return_value=conflicting_order)):
        response = client.get("/api/v1/billing/notify?id=123456")
    assert response.status_code == 404
    assert fake_session.order.status == "pending"


def test_stripe_webhook_requires_persisted_checkout_session_id(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    fake_session.order = _promotion_order(provider_ref=None)
    with patch("stripe.Webhook.construct_event", return_value=_promotion_event()):
        response = client.post(
            "/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"}
        )
    assert response.status_code == 400
    assert fake_session.order.status == "pending"
    assert fake_session.listing.promoted_tier is None


def test_duplicate_stripe_event_id_is_acknowledged_once(client, monkeypatch, fake_session):
    _set_stripe_keys(monkeypatch)
    fake_session.order = _promotion_order()
    with patch("stripe.Webhook.construct_event", return_value=_promotion_event()):
        first = client.post(
            "/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"}
        )
        first_until = fake_session.listing.promoted_until
        second = client.post(
            "/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"}
        )
    assert first.status_code == second.status_code == 200
    assert second.json().get("duplicate") is True
    assert fake_session.listing.promoted_until == first_until
    assert list(fake_session.webhook_events) == ["evt_123"]


def test_stale_stripe_subscription_event_cannot_revert_newer_state(
    client, monkeypatch, fake_session
):
    _set_stripe_keys(monkeypatch)
    fake_session.company.stripe_subscription_id = "sub_live_123"
    fake_session.company.subscription_tier = "ai"
    fake_session.order = BillingPaymentOrderModel(
        id=uuid4(),
        order_ref="sub-recovery-order",
        provider="stripe",
        provider_ref="cs_sub",
        stripe_subscription_id="sub_live_123",
        stripe_last_event_created=200,
        user_id=USER_ID,
        company_id=COMPANY_ID,
        product_kind="subscription",
        tier="ai",
        amount_cents=2900,
        currency="EUR",
        status="applied",
    )
    event = {
        "id": "evt_stale",
        "type": "customer.subscription.updated",
        "created": 199,
        "data": {"object": {"id": "sub_live_123", "status": "unpaid"}},
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        response = client.post(
            "/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "ok"}
        )
    assert response.status_code == 200
    assert fake_session.company.subscription_tier == "ai"
    assert fake_session.order.stripe_last_event_created == 200
