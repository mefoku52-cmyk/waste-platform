"""API tests pre exception handlers — 404, 422, 401."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_404_for_unknown_endpoint(client):
    """Neznámy endpoint → 404."""
    response = await client.get("/api/v1/this-does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_422_for_invalid_body(client):
    """Login s nesprávnym typom → 422."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": 12345, "password": "x"},  # email má byť string
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_401_for_missing_auth(client):
    """Chránený endpoint bez Authorization → 401."""
    response = await client.get("/api/v1/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_401_for_invalid_scheme(client):
    """Authorization s neplatným schémou → 401."""
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},  # Basic, nie Bearer
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_405_for_wrong_method(client):
    """Nesprávna HTTP metóda → 405."""
    response = await client.delete("/health")  # health je len GET
    assert response.status_code == 405
