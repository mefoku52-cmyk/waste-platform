"""Unit tests pre InMemoryRateLimiter."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.shared.infrastructure.rate_limiter import InMemoryRateLimiter


def _make_request(host: str = "127.0.0.1", path: str = "/api/test"):
    """Vytvorí mock Request objekt pre testovanie."""
    request = MagicMock()
    request.client.host = host
    request.url.path = path
    return request


@pytest.mark.asyncio
async def test_allows_under_limit():
    """Prvé N requesty prejdú."""
    limiter = InMemoryRateLimiter(requests_per_window=3, window_seconds=60)
    for _ in range(3):
        await limiter.enforce(_make_request())
    # Žiadna výnimka = OK


@pytest.mark.asyncio
async def test_blocks_over_limit():
    """(N+1). request zlyhá s 429."""
    limiter = InMemoryRateLimiter(requests_per_window=3, window_seconds=60)
    for _ in range(3):
        await limiter.enforce(_make_request())

    with pytest.raises(HTTPException) as exc:
        await limiter.enforce(_make_request())
    assert exc.value.status_code == 429
    headers = exc.value.headers or {}
    assert "Retry-After" in headers


@pytest.mark.asyncio
async def test_different_clients_independent():
    """Rôzni klienti majú nezávislé limity."""
    limiter = InMemoryRateLimiter(requests_per_window=2, window_seconds=60)
    for _ in range(2):
        await limiter.enforce(_make_request(host="10.0.0.1"))

    # Iný klient nie je ovplyvnený
    await limiter.enforce(_make_request(host="10.0.0.2"))
    # Žiadna výnimka


@pytest.mark.asyncio
async def test_different_paths_independent():
    """Rôzne cesty pre toho istého klienta majú nezávislé limity."""
    limiter = InMemoryRateLimiter(requests_per_window=2, window_seconds=60)
    for _ in range(2):
        await limiter.enforce(_make_request(path="/api/a"))

    await limiter.enforce(_make_request(path="/api/b"))
    # Žiadna výnimka
