from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text as _sql_text

from app.core.config import settings
from app.core.http_exception_handlers import register_http_exception_handlers
from app.shared.infrastructure.scheduler import start_scheduler, stop_scheduler
from app.shared.presentation.rate_limit_middleware import RateLimitMiddleware
from app.shared.presentation.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger("cmep.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting CMEP app env=%s docs=%s",
        settings.app_env,
        settings.ENABLE_PUBLIC_DOCS,
    )
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
        logger.info("Stopping CMEP app")


def _cors_origins() -> list[str]:
    """Vrati zoznam povolenych CORS origins.

    Zdroj pravdy: settings.CORS_ORIGINS (env CORS_ORIGINS alebo
    CORS_ALLOWED_ORIGINS). Dev domény sa pridávajú len v development.
    Ak by env bolo prazdne, drzime bezpecny produkcny fallback.
    """
    origins: list[str] = []
    seen: set[str] = set()

    def _add(value: str) -> None:
        v = value.strip()
        if v and v not in seen:
            seen.add(v)
            origins.append(v)

    # settings.cors_origin_list() moze vratit legacy string s ciarkami ako
    # jeden prvok (stary default), tak kazdy prvok rozdelime.
    for item in settings.cors_origin_list():
        for part in str(item).split(","):
            _add(part)

    # Bezpecny produkcny fallback, ak by env bolo prazdne.
    if not origins:
        _add("https://trc-cmep.sk")
        _add("https://www.trc-cmep.sk")

    if settings.is_development:
        _add("http://127.0.0.1:3001")
        _add("http://localhost:3001")

    return origins


def create_app() -> FastAPI:
    app = FastAPI(
        redirect_slashes=False,
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs" if settings.ENABLE_PUBLIC_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_PUBLIC_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_PUBLIC_DOCS else None,
        root_path=settings.ROOT_PATH or "",
        lifespan=lifespan,
    )

    register_http_exception_handlers(app)

    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request, exc):
        # Vratime len loc + msg, NIE `input` (leak user vstupu / DoS vektor).
        clean = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", "")} for e in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": clean})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )

    # Pridane PO CORS -> v LIFO poradi je SecurityHeaders najvyssi,
    # takze sa aplikuje aj na CORS preflight (OPTIONS) odpovede.
    # RateLimit je vnutri SecurityHeaders (LIFO), aby 429 odpovede mali hlavicky.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    mounted: list[str] = []
    skipped: list[dict[str, str]] = []

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
            "env": settings.app_env,
            "mounted_routers": mounted,
            "skipped_routers": skipped,
        }

    @app.get("/ready")
    async def ready():
        """Kubernetes-style readiness probe.

        Returns 200 only when the app can actually serve traffic:
        database reachable via SELECT 1 and Redis responds to PING.
        Returns 503 otherwise with a breakdown of which dependency
        failed. Never raises.
        """
        from fastapi.responses import JSONResponse

        checks: dict[str, str] = {}

        # --- Database ---
        try:
            from app.shared.infrastructure.db.session import (
                async_session_factory,
            )

            async with async_session_factory() as session:
                await session.execute(_sql_text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"fail: {type(exc).__name__}"

        # --- Redis ---
        try:
            import redis.asyncio as _redis

            client = _redis.from_url(settings.REDIS_URL, socket_timeout=2)
            await client.ping()  # ty: ignore[invalid-await]
            await client.aclose()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"fail: {type(exc).__name__}"

        healthy = all(v == "ok" or v == "disabled" for v in checks.values())
        status_code = 200 if healthy else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if healthy else "not-ready",
                "checks": checks,
                "env": settings.app_env,
                "version": settings.app_version,
            },
        )

    try:
        from app.shared.presentation.api_router import api_router

        pref = getattr(api_router, "prefix", "") or ""
        if pref.startswith("/api"):
            app.include_router(api_router)
        else:
            app.include_router(api_router, prefix="/api/v1")
        mounted.append("shared.api_router")
    except Exception as e:
        logger.exception("Failed to include shared.api_router")
        skipped.append({"module": "shared.api_router", "error": str(e)})

    app.state.mounted_routers = mounted
    app.state.skipped_routers = skipped

    logger.info("Mounted routers=%s skipped=%s", mounted, skipped)

    return app


app = create_app()
