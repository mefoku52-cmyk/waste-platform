"""Billing status endpoint — bez konfigurácie vracia configured=false."""

from uuid import uuid4

import pytest
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


def test_billing_status_unconfigured(client):
    r = client.get("/api/v1/billing/status")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "gopay"
    assert body["configured"] is False
    assert body["tier"] == "pro"
