"""Admin router smoke tests — auth guards and OpenAPI registration."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_stats_without_auth_401(client):
    r = client.get("/api/v1/admin/stats")
    assert r.status_code == 401


def test_users_list_without_auth_401(client):
    r = client.get("/api/v1/admin/users")
    assert r.status_code == 401


def test_lead_outreach_pending_without_auth_401(client):
    r = client.get("/api/v1/admin/lead-outreach/pending")
    assert r.status_code == 401


def test_discover_daily_without_auth_401(client):
    r = client.post("/api/v1/admin/lead-outreach/discover-daily", json={})
    assert r.status_code == 401


def test_backfill_emails_without_auth_401(client):
    r = client.post(
        "/api/v1/admin/lead-outreach/backfill-emails",
        json={},
    )
    assert r.status_code == 401


def test_user_summary_without_auth_401(client):
    r = client.get("/api/v1/admin/users/some-id/summary")
    assert r.status_code == 401


def test_user_activity_without_auth_401(client):
    r = client.get("/api/v1/admin/users/some-id/activity")
    assert r.status_code == 401


def test_openapi_has_admin_stats():
    schema = app.openapi()
    assert "/api/v1/admin/stats" in schema["paths"]


def test_openapi_has_backfill_endpoint():
    schema = app.openapi()
    assert "/api/v1/admin/lead-outreach/backfill-emails" in schema["paths"]


def test_openapi_has_discover_endpoint():
    schema = app.openapi()
    assert "/api/v1/admin/lead-outreach/discover-daily" in schema["paths"]


def test_openapi_has_user_summary():
    schema = app.openapi()
    assert "/api/v1/admin/users/{user_id}/summary" in schema["paths"]


def test_openapi_has_user_activity():
    schema = app.openapi()
    assert "/api/v1/admin/users/{user_id}/activity" in schema["paths"]


def test_openapi_has_prediction_endpoints():
    schema = app.openapi()
    assert "/api/v1/prediction/access" in schema["paths"]
    assert "/api/v1/prediction/predict" in schema["paths"]


def test_openapi_has_lead_outreach_send_endpoint():
    schema = app.openapi()
    assert "/api/v1/admin/lead-outreach/candidates/{candidate_id}/send" in schema["paths"]


def test_openapi_has_lead_outreach_skip_endpoint():
    schema = app.openapi()
    assert "/api/v1/admin/lead-outreach/candidates/{candidate_id}/skip" in schema["paths"]
