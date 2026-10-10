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

# Pravidla (metoda, path-prefix, limit, okno_v_sekundach, meno).
# Ak na jeden path sedi viac pravidiel, aplikuju sa VSETKY (nezavisle
# pocitadla) — dvojica burst + hourly da kratsky spam-strop aj dlhodoby
# cooldown.
_RULES = [
    ("POST", "/auth/2fa/login", 10, 60, "2fa-login-ip"),
    ("POST", "/agent-platform/control/mode", 20, 60, "control-mode"),
    ("POST", "/agent-platform/control/emergency/activate", 5, 60, "control-emergency-activate"),
    ("POST", "/agent-platform/control/emergency/release", 5, 60, "control-emergency-release"),
    # AI chat — LLM requesty su drahe: burst 20/min + 120/hod.
    ("POST", "/agent-platform/chat", 20, 60, "agent-chat-ip"),
    ("POST", "/agent-platform/chat", 120, 3600, "agent-chat-hourly"),
    # Voice (Telnyx transcribe / live token) — platene API: burst 10/min + 60/hod.
    ("POST", "/agent-platform/voice", 10, 60, "agent-voice-ip"),
    ("POST", "/agent-platform/voice", 60, 3600, "agent-voice-hourly"),
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


def _match_rules(method, path) -> list[tuple[int, int, str]]:
    """Vrati VSETKY pravidla sediace na metodu+path (burst aj hourly)."""
    normalized = _normalize_path(path)
    matched = []
    for rule_method, rule_path, limit, period, name in _RULES:
        if method != rule_method:
            continue
        if rule_path.endswith("/"):
            if normalized.startswith(rule_path):
                matched.append((limit, period, name))
        else:
            if normalized == rule_path or normalized.startswith(rule_path + "/"):
                matched.append((limit, period, name))
    return matched


def _match_rule(method, path):
    """Backward-compat: prve matchnute pravidlo (alebo None).

    Middleware pouziva _match_rules (vsetky pravidla); tento single-match
    wrapper ostava kvoli existujucim testom a volacom.
    """
    rules = _match_rules(method, path)
    return rules[0] if rules else None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rules = _match_rules(request.method, request.url.path)
        if not rules:
            return await call_next(request)
        for limit, period, name in rules:
            try:
                check_rate_limit(f"{name}:{client_ip(request)}", limit=limit, period=period)
            except HTTPException as exc:
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)
