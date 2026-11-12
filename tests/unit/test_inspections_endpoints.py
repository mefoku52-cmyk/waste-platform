"""HTTP gating testy pre inspections router (auth, internal key fail-closed)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_inspection_requires_auth(client):
    r = client.post("/api/v1/inspections", json={"listingId": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 401


def test_join_requires_auth(client):
    r = client.post("/api/v1/inspections/join", json={})
    assert r.status_code == 401


def test_get_inspection_requires_auth(client):
    r = client.get("/api/v1/inspections/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 401


def test_verify_fail_closed_without_internal_key(client):
    """Bez konfiguracie (kluc je v testoch prazdny) je verify fail-closed 403."""
    r = client.get(
        "/api/v1/inspections/00000000-0000-0000-0000-000000000000/verify",
        params={"sub": "x", "role": "publisher"},
    )
    assert r.status_code == 403


def test_events_fail_closed_without_internal_key(client):
    r = client.post(
        "/api/v1/inspections/events",
        json={
            "eventUid": "0123456789abcdef",
            "inspectionId": "00000000-0000-0000-0000-000000000000",
            "eventType": "inspection_started",
        },
    )
    assert r.status_code == 403
