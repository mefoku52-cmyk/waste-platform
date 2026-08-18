import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.shared.infrastructure.db.base import Base
from app.shared.infrastructure.db import register_models  # noqa: F401
from app.shared.infrastructure.db.session import engine
from app.shared.presentation.api_router import api_router
from app.shared.presentation.exception_handlers import register_exception_handlers
from app.shared.presentation.health_router import router as health_router
from app.shared.presentation.metrics_router import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logging.info("Shutting down...")


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

is_production = bool(getattr(settings, "is_production", False))
root_path = getattr(settings, "root_path", "") or ""

servers = []
if not is_production:
    servers.append({"url": "/", "description": "Local development"})
if root_path:
    servers.append({"url": root_path, "description": "Reverse proxy root path"})

app = FastAPI(
    title="Circular Materials Exchange Platform API",
    version="0.1.0",
    description="CMEP - Platform for circular materials exchange",
    lifespan=lifespan,
    root_path=root_path,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    servers=servers or None,
)

cors_origins = [item.strip() for item in settings.cors.allowed_origins if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
)

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(api_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "CMEP API",
        "version": "0.1.0",
        "status": "operational",
        "docs": None if is_production else (f"{root_path}/docs" if root_path else "/docs"),
        "openapi": None if is_production else (f"{root_path}/openapi.json" if root_path else "/openapi.json"),
        "health": f"{root_path}/health" if root_path else "/health",
    }
