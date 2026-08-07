#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

echo "Opravujem importy pre config..."

# 1. Odstránenie duplicitného adresára config
rm -rf backend/app/core/config/
rm -f backend/app/core/config.py

# 2. Vytvorenie správneho config.py
cat > backend/app/core/config.py << 'CONFIG'
"""Konfigurácia aplikácie."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Nastavenia aplikácie."""

    # Projekt
    PROJECT_NAME: str = "RecycleHub API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API pre obehové hospodárstvo - správa ponúk druhotných surovín"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Prostredie
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Databáza
    DATABASE_URL: str = Field(default="postgresql://recyclehub:recyclehub@localhost:5432/recyclehub", env="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Security
    SECRET_KEY: str = Field(default="supersecretkeyforrecyclehub2024", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )

    # Allowed hosts
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")

    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(default="", env="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@recyclehub.sk", env="EMAIL_FROM")

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")

    # Monitoring
    PROMETHEUS_MULTIPROC_DIR: str = Field(
        default="/tmp/prometheus_multiproc",
        env="PROMETHEUS_MULTIPROC_DIR"
    )

    # GDPR
    GDPR_ENABLED: bool = Field(default=True, env="GDPR_ENABLED")
    GDPR_COOKIE_CONSENT: bool = Field(default=True, env="GDPR_COOKIE_CONSENT")

    # Stripe
    STRIPE_SECRET_KEY: str = Field(default="", env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
CONFIG

# 3. Oprava __init__.py pre core
cat > backend/app/core/__init__.py << 'CORE'
"""Core moduly aplikácie."""

from app.core.database import Base, engine, AsyncSessionLocal, get_db
from app.core.config import settings
from app.core.logging import setup_logging

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "settings",
    "setup_logging",
]
CORE

# 4. Oprava health.py
cat > backend/app/api/v1/health.py << 'HEALTH'
"""Health check endpointy."""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def health_check() -> dict:
    """Základný health check."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Kontrola pripravenosti aplikácie."""
    try:
        await db.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    
    return {
        "status": "ready" if db_ok else "not_ready",
        "database": db_ok,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/live")
async def liveness_check() -> dict:
    """Kontrola živosti aplikácie."""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }
HEALTH

echo "✅ Config importy opravené"
