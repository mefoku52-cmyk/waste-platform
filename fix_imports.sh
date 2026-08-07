#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

# Oprava importov v main.py
cat > backend/app/main.py << 'MAIN'
"""Hlavný vstupný bod FastAPI aplikácie."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging import setup_logging

# Import models pre vytvorenie tabuliek
from app.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Správa životného cyklu aplikácie."""
    # Startup
    setup_logging()
    
    # Vytvorenie databázových tabuliek
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    await engine.dispose()

# Inicializácia aplikácie
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Vlastná Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Vlastná Swagger UI stránka."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.PROJECT_NAME} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

# OpenAPI dokumentácia
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    """Vlastný OpenAPI endpoint."""
    return get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Kontrola stavu aplikácie."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Koreňový endpoint."""
    return {
        "message": f"Vitajte v {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }

# Pridanie middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="recyclehub_session",
)

# Inklúzia API routerov
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
MAIN

# Oprava database.py
cat > backend/app/core/database.py << 'DATABASE'
"""Databázová vrstva."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Asynchrónny engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Asynchrónna session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base pre modely
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Získanie databázovej session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
DATABASE

# Oprava models/__init__.py
cat > backend/app/models/__init__.py << 'MODELS'
"""Databázové modely."""

from app.core.database import Base
from app.models.base import BaseModel

# Export všetkých modelov
__all__ = [
    "Base",
    "BaseModel",
]
MODELS

# Vytvorenie __init__.py pre core
cat > backend/app/core/__init__.py << 'CORE'
"""Core moduly aplikácie."""
CORE

echo "Importy opravené"
