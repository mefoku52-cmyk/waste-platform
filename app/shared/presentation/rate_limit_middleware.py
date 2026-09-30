"""Global rate-limiting middleware.

Runs BEFORE Pydantic body validation so that malformed requests still get
rate-limited (an earlier version placed check_rate_limit inside endpoint
handlers, which meant invalid bodies bypassed the limiter entirely).

Registered in app/main.py AFTER CORSMiddleware and BEFORE
SecurityHeadersMiddleware, so the middleware stack (LIFO) is:

    request  -> SecurityHeaders -> RateLimit -> CORS -> endpoint
    response <- SecurityHeaders <- RateLimit <- CORS <- endpoint
"""

from __future__ import annotations

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.shared.infrastructure.rate_limit import check_rate_limit, client_ip

_RULES = [
    ("POST", "/auth/2fa/login", 10, 60, "2fa-login-ip"),
    ("POST", "/agent-platform/control/mode", 20, 60, "control-mode"),
    ("POST", "/agent-platform/control/emergency/activate", 5, 60, "control-emergency-activate"),
    ("POST", "/agent-platform/control/emergency/release", 5, 60, "control-emergency-release"),
    ("GET", "/admin/", 120, 60, "admin-read"),
    ("POST", "/admin/", 30, 60, "admin-write"),
    ("PATCH", "/admin/", 30, 60, "admin-write"),
    ("DELETE", "/admin/", 30, 60, "admin-write"),
    ("POST", "/chat/threads/", 60, 60, "chat-message"),
    ("POST", "/chat/threads", 30, 60, "chat-create"),
    ("POST", "/uploads/", 20, 60, "uploads"),
    ("POST", "/listings", 30, 60, "listings-create"),
    ("PATCH", "/listings/", 60, 60, "listings-write"),
    ("DELETE", "/listings/", 30, 60, "listings-delete"),
    ("POST", "/inquiries", 30, 60, "inquiries-create"),
    # Registracia — bot spam ochrana. 3 registracie / hodinu / IP.
    ("POST", "/users", 3, 3600, "user-register-ip"),
]

_API_PREFIXES = ("/api/v1", "/api")


def _normalize_path(path):
    for prefix in _API_PREFIXES:
        if path == prefix:
            return "/"
        if path.startswith(prefix + "/"):
            return path[len(prefix) :]
    return path


def _match_rule(method, path):
    normalized = _normalize_path(path)
    for rule_method, rule_path, limit, period, name in _RULES:
        if method != rule_method:
            continue
        if rule_path.endswith("/"):
            if normalized.startswith(rule_path):
                return (limit, period, name)
        else:
            if normalized == rule_path or normalized.startswith(rule_path + "/"):
                return (limit, period, name)
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rule = _match_rule(request.method, request.url.path)
        if rule is None:
            return await call_next(request)
        limit, period, name = rule
        try:
            check_rate_limit(f"{name}:{client_ip(request)}", limit=limit, period=period)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)
