"""Unit tests pre exception handlers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.http_exception_handlers import register_http_exception_handlers
from app.shared.domain.exceptions import (
    NotFoundDomainError,
    UnauthorizedDomainError,
    ValidationDomainError,
)


@pytest.fixture
def test_app():
    """Minimal FastAPI app s registrovanými handlermi."""
    app = FastAPI()
    register_http_exception_handlers(app)

    @app.get("/raise-not-found")
    async def _raise_not_found():
        raise NotFoundDomainError("Item not found")

    @app.get("/raise-unauthorized")
    async def _raise_unauthorized():
        raise UnauthorizedDomainError("No access")

    @app.get("/raise-validation")
    async def _raise_validation():
        raise ValidationDomainError("Invalid input")

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app, raise_server_exceptions=False)


def test_not_found_returns_404(client):
    """NotFoundDomainError → 404."""
    response = client.get("/raise-not-found")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body


def test_unauthorized_returns_401(client):
    """UnauthorizedDomainError → 401."""
    response = client.get("/raise-unauthorized")
    assert response.status_code == 401
    body = response.json()
    assert "detail" in body


def test_validation_returns_422(client):
    """ValidationDomainError → 422."""
    response = client.get("/raise-validation")
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
