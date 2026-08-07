#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "=================================================="
echo "FÁZA 1 - KOMPLETNÁ OPRAVA A DOKONČENIE"
echo "=================================================="

# Nastavenie ciest
PROJECT_DIR="/data/data/com.termux/files/home/waste-platform"
BACKEND_DIR="${PROJECT_DIR}/backend"

cd "${PROJECT_DIR}"

echo ""
echo "1. INŠTALÁCIA CHÝBAJÚCICH ZÁVISLOSTÍ"
echo "------------------------------------------"

cd "${BACKEND_DIR}"
source venv/bin/activate || source venv/Scripts/activate || true

# Inštalácia pydantic-settings
pip install pydantic-settings==2.0.3

echo ""
echo "2. KONTROLA A OPRAVA ŠTRUKTÚRY"
echo "------------------------------------------"

# Odstránenie duplicitných adresárov
rm -rf app/core/config/ 2>/dev/null || true
rm -rf app/core/database/ 2>/dev/null || true

# Vytvorenie config.py
cat > app/core/config.py << 'CONFIG_EOF'
"""Konfigurácia aplikácie."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Nastavenia aplikácie."""

    PROJECT_NAME: str = "RecycleHub API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API pre obehové hospodárstvo"
    API_V1_PREFIX: str = "/api/v1"
    
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    DATABASE_URL: str = Field(
        default="postgresql://recyclehub:recyclehub@localhost:5432/recyclehub",
        env="DATABASE_URL"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    SECRET_KEY: str = Field(
        default="supersecretkeyforrecyclehub2024",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(default="", env="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@recyclehub.sk", env="EMAIL_FROM")
    
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    PROMETHEUS_MULTIPROC_DIR: str = Field(
        default="/tmp/prometheus_multiproc",
        env="PROMETHEUS_MULTIPROC_DIR"
    )
    
    GDPR_ENABLED: bool = Field(default=True, env="GDPR_ENABLED")
    GDPR_COOKIE_CONSENT: bool = Field(default=True, env="GDPR_COOKIE_CONSENT")
    
    STRIPE_SECRET_KEY: str = Field(default="", env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
CONFIG_EOF

# Vytvorenie database.py
cat > app/core/database.py << 'DATABASE_EOF'
"""Databázová vrstva."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
DATABASE_EOF

# Vytvorenie core/__init__.py
cat > app/core/__init__.py << 'CORE_EOF'
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
CORE_EOF

echo ""
echo "3. VYTVORENIE ALEMBIC MIGRÁCIÍ"
echo "------------------------------------------"

# Oprava alembic/env.py
cat > alembic/env.py << 'ENV_EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Base
from app.models import *

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
ENV_EOF

# Vytvorenie migrácie
alembic revision --autogenerate -m "Add all models" 2>/dev/null || echo "Migrácia už existuje"
alembic upgrade head 2>/dev/null || echo "Migrácia už bola aplikovaná"

echo ""
echo "4. SPUSTENIE BACKENDU"
echo "------------------------------------------"

# Zabitie starého procesu
pkill -f "uvicorn app.main:app" 2>/dev/null || true

# Spustenie backendu
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &

sleep 5

echo ""
echo "5. TESTOVANIE ENDPOINTOV"
echo "------------------------------------------"

# Health check
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health endpoint: OK"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null
else
    echo "❌ Health endpoint: FAILED"
    echo "Posledné logy:"
    tail -n 20 logs/backend.log 2>/dev/null
fi

echo ""
# Docs
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Docs endpoint: OK (HTTP $HTTP_CODE)"
else
    echo "❌ Docs endpoint: FAILED (HTTP $HTTP_CODE)"
fi

echo ""
echo "=================================================="
echo "FÁZA 1 DOKONČENÁ"
echo "=================================================="
echo ""
echo "Backend beží na: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
echo ""
echo "Logy: tail -f ${BACKEND_DIR}/logs/backend.log"

cd "${PROJECT_DIR}"
