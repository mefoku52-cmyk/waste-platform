"""API tests pre health a metrics endpointy."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """/health vráti 200 + JSON."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_openapi_endpoint(client):
    """/openapi.json vráti validnú schému."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert len(data["paths"]) > 10


@pytest.mark.asyncio
async def test_login_no_body_returns_422(client):
    """Login bez credentials → 422."""
    response = await client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_creds_returns_401(client):
    """Login so zlými credentials → 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nope@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_no_token_returns_401(client):
    """Chránený endpoint bez tokenu → 401."""
    response = await client.get("/api/v1/companies")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_bad_token_returns_401(client):
    """Chránený endpoint s neplatným tokenom → 401."""
    response = await client.get(
        "/api/v1/companies",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401
