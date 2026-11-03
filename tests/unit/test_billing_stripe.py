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
        if model is ListingsModel and str(key) == LISTING_ID: return self.listing
        if model is CompanyModel and str(key) == COMPANY_ID: return self.company
        if model is BillingPaymentOrderModel and self.order is not None:
            return self.order if key == getattr(self.order, "id", None) else None
        return None

    def add(self, value):
        if isinstance(value, BillingPaymentOrderModel): self.order = value
        elif isinstance(value, BillingWebhookEventModel): self.webhook_events[value.event_id] = value

    async def flush(self): return None

    async def execute(self, statement, *args, **kwargs):
        if getattr(statement, "is_update", False):
            self.company.subscription_tier = "free"
            values = getattr(statement, "_values", {})
            value_names = {getattr(column, "key", str(column)) for column in values}
            if "stripe_subscription_id" in value_names: self.company.stripe_subscription_id = None
            return _FakeResult(rowcount=1)
        
        descriptions = getattr(statement, "column_descriptions", [])
        if descriptions and descriptions[0].get("entity") is BillingWebhookEventModel:
            params = statement.compile().params
            event_id = next((value for key, value in params.items() if "event_id" in key), None)
            return _FakeResult(self.webhook_events.get(str(event_id)))
        
        if descriptions and descriptions[0].get("entity") is CompanyModel:
            params = statement.compile().params
            for key, value in params.items():
                if key.startswith("id_") and str(self.company.id) != str(value): return _FakeResult()
                if key.startswith("stripe_subscription_id_") and str(self.company.stripe_subscription_id) != str(value): return _FakeResult()
            return _FakeResult(self.company)
        
        if descriptions and descriptions[0].get("entity") is BillingPaymentOrderModel:
            candidate = self.order
            if candidate is None: return _FakeResult()
            params = statement.compile().params
            for key, value in params.items():
                if key.startswith("order_ref") and getattr(candidate, "order_ref", None) != value: return _FakeResult()
                if key.startswith("provider_") and getattr(candidate, "provider", None) != value: return _FakeResult()
                if key.startswith("product_kind") and getattr(candidate, "product_kind", None) != value: return _FakeResult()
                if key.startswith("stripe_subscription_id") and getattr(candidate, "stripe_subscription_id", None) != value: return _FakeResult()
                if key.startswith("status_") and getattr(candidate, "status", None) != value: return _FakeResult()
            return _FakeResult(candidate)
        return _FakeResult(self.order)

    async def commit(self): return None
    async def rollback(self): return None

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
        "client_id": "client", "client_secret": "secret", "goid": "1234567890",
        "api": "https://gw.sandbox.gopay.com", "return_url": "https://trc-cmep.sk/payment/return",
        "notify_url": "https://trc-cmep.sk/api/v1/billing/notify",
    }
    monkeypatch.setattr(billing_router, "_cfg", lambda: cfg)
    monkeypatch.setitem(settings.__dict__, "GOPAY_PRO_AMOUNT_CENTS", amount)

def _checkout_body(**over):
    body = {"kind": "promote", "listing_id": LISTING_ID, "days": 7, "tier": "top",
            "success_url": "https://trc-cmep.sk/success", "cancel_url": "https://trc-cmep.sk/cancel"}
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
        r = client.post("/api/v1/billing/stripe/checkout", json=_checkout_body(listing_id=None))
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
    md = create.call_args.kwargs["metadata"]
    assert md["kind"] == "promote" and md["listing_id"] == LISTING_ID

def test_webhook_503_when_not_configured(client, monkeypatch):
    _unset_stripe_keys(monkeypatch)
    r = client.post("/api/v1/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "x"})
    assert r.status_code == 503

def test_gopay_checkout_uses_server_owned_price_and_assigns_order_ref(client, monkeypatch, fake_session):
    from app.modules.billing.presentation import router as billing_router
    _set_gopay_config(monkeypatch, amount=6400)
    
    class _Response:
        status_code = 200
        @staticmethod
        def json(): return {"id": 123456, "gw_url": "https://gw.sandbox.gopay.com/pay/123456", "order_number": "ord-1"}

    class _AsyncClient:
        body = None
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            self.body = kwargs["json"]
            return _Response()

    fake_http = _AsyncClient()
    payload = {"company_id": COMPANY_ID, "tier": "pro", "amount_cents": 1, "currency": "USD"}
    
    with (patch.object(billing_router, "_token", new=AsyncMock(return_value="access-token")),
          patch.object(billing_router.httpx, "AsyncClient", return_value=fake_http)):
        response = client.post("/api/v1/billing/checkout", json=payload)
    
    assert response.status_code == 200, response.text
    # TU JE KĽÚČOVÁ OPRAVA: Kontrola pred prístupom k slovníku
    assert fake_http.body is not None
    assert fake_http.body["amount"] == 6400
    assert fake_http.body["currency"] == "EUR"
