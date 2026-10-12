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
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import stripe
from fastapi.testclient import TestClient

from app.main import app
from app.shared.presentation.auth_dependencies import require_current_user


class _FakeUser:
    def __init__(self):
        self.id = str(uuid4())
        self.email = "test@example.com"
        self.isPlatformAdmin = False
        self.memberships = []


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _override_auth():
    app.dependency_overrides[require_current_user] = lambda: _FakeUser()
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


def _checkout_body(**over):
    body = {
        "kind": "promote",
        "listing_id": "list-1",
        "days": 7,
        "tier": "top",
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel",
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
    assert md["listing_id"] == "list-1"
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


def test_webhook_promotes_listing_on_completed(client, monkeypatch):
    _set_stripe_keys(monkeypatch)
    fake_session = MagicMock()

    with (
        patch(
            "stripe.Webhook.construct_event",
            return_value={
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "metadata": {
                            "kind": "promote",
                            "listing_id": "list-42",
                            "days": "30",
                            "tier": "gold",
                        }
                    }
                },
            },
        ),
        patch(
            "app.modules.listings.presentation.dependencies.get_listings_service",
            return_value=AsyncMock(),
        ) as get_svc,
        patch(
            "app.modules.billing.presentation.router.get_db_session",
            return_value=fake_session,
        ),
    ):
        r = client.post(
            "/api/v1/billing/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "ok"},
        )

    assert r.status_code == 200, r.text
    assert r.json() == {"received": True}
    get_svc.assert_called_once()
    svc = get_svc.return_value
    svc.promote.assert_awaited_once()


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
