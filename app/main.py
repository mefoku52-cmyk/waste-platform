from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.http_exception_handlers import register_http_exception_handlers
from app.shared.infrastructure.scheduler import start_scheduler, stop_scheduler
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
    raw = settings.CORS_ORIGINS
    if isinstance(raw, list):
        origins = [str(item).strip() for item in raw if str(item).strip()]
    elif isinstance(raw, str) and raw.strip():
        origins = [part.strip() for part in raw.split(",") if part.strip()]
    else:
        origins = []
    for extra in (
        "http://127.0.0.1:3001",
        "http://localhost:3001",
        "https://trc-cmep.sk",
        "https://www.trc-cmep.sk",
    ):
        if extra not in origins:
            origins.append(extra)
    return origins


def create_app() -> FastAPI:
    app = FastAPI(
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
