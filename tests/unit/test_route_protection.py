"""Ensure every non-public /api/v1 route requires authentication."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi.routing import APIRoute

from app.main import app

PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/api/v1/integrations/health"),
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/metrics"),
        ("GET", "/api/v1/auth/browser/csrf"),
    }
)


def _iter_api_routes() -> Iterator[tuple[str, str, APIRoute]]:
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if not path.startswith("/api/v1/"):
            continue
        for method in route.methods or ():
            if method in {"HEAD", "OPTIONS"}:
                continue
            yield method, path, route


def _has_auth(route: APIRoute) -> bool:
    for dep in route.dependant.dependencies:
        name = getattr(dep.call, "__name__", None) if dep.call else None
        if name in {"require_current_user", "require_platform_admin"}:
            return True
    return False


def test_every_non_public_route_requires_authentication():
    offenders: list[str] = []
    for method, path, route in _iter_api_routes():
        if (method, path) in PUBLIC_ROUTES:
            continue
        if not _has_auth(route):
            offenders.append(f"{method} {path}")
    assert not offenders, "Unauthenticated /api/v1 routes not in PUBLIC_ROUTES:\n  " + "\n  ".join(
        sorted(offenders)
    )
