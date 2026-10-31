"""Automated route-protection guard (hardening gate 2).

Enumerates every ``/api/v1`` route registered on the app and asserts that each
one is EITHER:

* explicitly public (listed in ``PUBLIC_ROUTES`` below), or
* protected by an authentication dependency
  (``require_current_user`` / ``require_admin`` / ``get_current_user_optional``).

This is a regression guard: if a new endpoint is added without authentication
and is not consciously added to ``PUBLIC_ROUTES``, this test fails and forces a
review. It also verifies that no network/maintenance endpoint accidentally
loses its guard.

FastAPI >= 0.141 keeps included routers lazy (``_IncludedRouter``), so the raw
``app.routes`` list is NOT flat. The walker below handles both the lazy form and
the classic flattened form.
"""

from __future__ import annotations

from fastapi.routing import APIRoute

try:  # FastAPI >= 0.141
    from fastapi.routing import _IncludedRouter as _LazyIncludedRouter
except ImportError:  # pragma: no cover - older FastAPI
    _LazyIncludedRouter = None  # type: ignore[assignment]

from app.main import app

_AUTH_DEP_NAMES = {
    "require_current_user",
    "require_admin",
    "get_current_user_optional",
}

# Endpoints that are intentionally reachable without a Bearer token.
# Adding a route here is a security decision, not a convenience.
PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        # --- auth entry points ---
        ("GET", "/api/v1/transport/offers"),
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/auth/refresh"),
        ("POST", "/api/v1/auth/forgot-password"),
        ("POST", "/api/v1/auth/reset-password"),
        ("POST", "/api/v1/auth/verify-email"),
        ("POST", "/api/v1/auth/resend-verification"),
        ("POST", "/api/v1/auth/2fa/login"),
        ("GET", "/api/v1/auth/browser/csrf"),
        ("POST", "/api/v1/auth/browser/login"),
        ("POST", "/api/v1/auth/browser/2fa/login"),
        ("POST", "/api/v1/auth/browser/refresh"),
        ("POST", "/api/v1/auth/browser/logout"),
        # --- registration ---
        ("POST", "/api/v1/users"),
        # --- public company directory (SEO) ---
        ("GET", "/api/v1/public/company-pages"),
        ("GET", "/api/v1/public/company-pages/{slug}"),
        ("GET", "/api/v1/public/company-pages/{slug}/assets/{file_id}"),
        ("POST", "/api/v1/public/company-pages/{slug}/contact"),
        # --- public landing/analytics ingestion ---
        ("POST", "/api/v1/events/contact"),
        ("POST", "/api/v1/analytics/acquisition/events"),
        # --- webhooks (verified by provider signature/secret) ---
        ("POST", "/api/v1/billing/stripe/webhook"),
        ("GET", "/api/v1/billing/notify"),
        ("POST", "/api/v1/billing/notify"),
        ("POST", "/api/v1/admin/telegram/webhook"),
        # --- infrastructure probes (static, no sensitive data) ---
        ("GET", "/api/v1/ops/health"),
        ("GET", "/api/v1/ops/ready"),
        ("GET", "/api/v1/metrics"),
        ("GET", "/api/v1/agent-platform/health"),
        ("GET", "/api/v1/agent-platform/control/health"),
        ("GET", "/api/v1/agent-platform/control/status"),
    }
)


def _iter_api_routes() -> list[tuple[str, str, APIRoute]]:
    """Return ``(method, path, route)`` for every ``/api/v1`` route."""
    found: list[tuple[str, str, APIRoute]] = []

    def walk(node: object, prefix: str) -> None:
        if _LazyIncludedRouter is not None and isinstance(node, _LazyIncludedRouter):
            ctx = getattr(node, "include_context", None)
            sub_prefix = prefix + (getattr(ctx, "prefix", "") or "")
            walk(getattr(node, "original_router", node), sub_prefix)
            return
        if isinstance(node, APIRoute):
            path = prefix + node.path
            for method in sorted(node.methods or []):
                found.append((method, path, node))
            return
        for child in getattr(node, "routes", []) or []:
            walk(child, prefix)

    walk(app, "")
    return [item for item in found if item[1].startswith("/api/v1")]


def _dependency_names(route: APIRoute) -> set[str]:
    names: set[str] = set()

    def walk(dependant: object) -> None:
        call = getattr(dependant, "call", None)
        if call is not None:
            names.add(getattr(call, "__name__", ""))
        for child in getattr(dependant, "dependencies", []) or []:
            walk(child)

    dependant = getattr(route, "dependant", None)
    if dependant is not None:
        walk(dependant)
    return names


def _has_auth(route: APIRoute) -> bool:
    return bool(_dependency_names(route) & _AUTH_DEP_NAMES)


def test_route_enumeration_is_non_trivial():
    """Sanity: the walker must actually find the API surface."""
    routes = _iter_api_routes()
    assert len(routes) > 100, f"only {len(routes)} routes enumerated — walker broke"


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


def test_public_allowlist_has_no_stale_entries():
    """Every allowlisted route must still exist (drop dead entries)."""
    known = {(method, path) for method, path, _ in _iter_api_routes()}
    stale = sorted(set(PUBLIC_ROUTES) - known)
    assert not stale, "PUBLIC_ROUTES contains routes that no longer exist:\n  " + "\n  ".join(
        f"{m} {p}" for m, p in stale
    )
