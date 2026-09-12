"""Unit tests pre health router."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_ok(client):
    """/health → 200 s ok statusom."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
    assert "mounted_routers" in data
    assert len(data["mounted_routers"]) > 0


@pytest.mark.asyncio
async def test_health_returns_env(client):
    """/health obsahuje env."""
    response = await client.get("/health")
    data = response.json()
    assert "env" in data
    assert data["env"] in ("development", "production", "test")


@pytest.mark.asyncio
async def test_health_skipped_routers_empty(client):
    """Všetky routery sú namountované."""
    response = await client.get("/health")
    data = response.json()
    assert "skipped_routers" in data
    assert data["skipped_routers"] == []
