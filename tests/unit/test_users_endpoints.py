"""Users endpoints + admin-only guards."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_users_requires_auth(client):
    r = client.get("/api/v1/users")
    assert r.status_code == 401


def test_create_user_fake_domain_422(client):
    r = client.post(
        "/api/v1/users",
        json={
            "email": "fake@b.c",
            "firstName": "A",
            "lastName": "B",
            "password": "12345678",
        },
    )
    # 422 validácia domény
    assert r.status_code == 422


def test_create_user_example_com_422(client):
    r = client.post(
        "/api/v1/users",
        json={
            "email": "fake@example.com",
            "firstName": "A",
            "lastName": "B",
            "password": "12345678",
        },
    )
    assert r.status_code == 422


def test_create_user_short_password_422(client):
    r = client.post(
        "/api/v1/users",
        json={
            "email": "ok@realdomena.com",
            "firstName": "A",
            "lastName": "B",
            "password": "short",
        },
    )
    assert r.status_code == 422


def test_get_user_requires_auth(client):
    r = client.get("/api/v1/users/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 401


def test_update_user_requires_auth(client):
    r = client.patch(
        "/api/v1/users/00000000-0000-0000-0000-000000000001",
        json={"firstName": "X"},
    )
    assert r.status_code == 401


def test_transition_user_status_requires_auth(client):
    r = client.patch(
        "/api/v1/users/00000000-0000-0000-0000-000000000001/status",
        json={"toStatus": "active"},
    )
    assert r.status_code == 401


def test_delete_user_requires_auth(client):
    r = client.delete("/api/v1/users/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 401


def test_openapi_has_users_endpoints():
    paths = app.openapi()["paths"]
    for p in [
        "/api/v1/users",
        "/api/v1/users/{user_id}",
        "/api/v1/users/{user_id}/status",
    ]:
        assert p in paths


def test_openapi_users_has_delete():
    paths = app.openapi()["paths"]
    # existuje DELETE /users/{user_id}
    assert "delete" in paths["/api/v1/users/{user_id}"]
