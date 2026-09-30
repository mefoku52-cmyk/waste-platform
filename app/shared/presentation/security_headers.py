"""Globálne bezpečnostné HTTP hlavičky pre FastAPI odpovede.

Pridáva sa ako middleware v app/main.py. Cieľom je, aby KAŽDÁ odpoveď z API
(vrátane chybových) mala základné bezpečnostné hlavičky. Next.js frontend má
vlastné hlavičky v next.config.js — toto pokrýva iba API vrstvu.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# CSP pre API: žiadne zdroje, žiadne iframy, žiadne skripty.
# API vracia len JSON, takže CSP môže byť striktné.
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"

_HEADERS = {
    # HSTS — 1 rok, vrátane subdomén. Podmienka: HTTPS (v produkcii vždy).
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    # Zamedzí clickjackingu (v novších browseroch je nahradené CSP frame-ancestors,
    # ale držíme oboje pre staršie browsery).
    "X-Frame-Options": "DENY",
    # Zamedzí MIME sniffing.
    "X-Content-Type-Options": "nosniff",
    # Referrer policy — neposielaj referrer na iné domény.
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Permissions policy — vypni všetko, čo API nepotrebuje.
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    # CSP pre API odpovede.
    "Content-Security-Policy": _API_CSP,
    # Info disclosure — odstrániť server identifikáciu, ktorú pridáva Starlette.
    "X-Permitted-Cross-Domain-Policies": "none",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for name, value in _HEADERS.items():
            # Nechceme prepísať, ak už nejaký handler nastavil vlastnú hodnotu.
            if name not in response.headers:
                response.headers[name] = value
        # Starlette pridáva "server: uvicorn" hlavičku — nechceme ju.
        # BaseHTTPMiddleware ju nezachytí, ale aspoň X-Powered-By odstránime.
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]
        return response
