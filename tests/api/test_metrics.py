"""API tests pre metrics endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_metrics_endpoint_exists(client):
    """Metrics endpoint odpovie (200 alebo 404 podľa config)."""
    response = await client.get("/metrics")
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Root endpoint odpovie."""
    response = await client.get("/")
    assert response.status_code in (200, 404)
