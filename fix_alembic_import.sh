#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

echo "Opravujem importy pre Alembic..."

# 1. Odstránenie duplicitného adresára database
rm -rf backend/app/core/database/
rm -f backend/app/core/database.py

# 2. Vytvorenie správneho database.py
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

# 4. Oprava alembic/env.py
cat > backend/alembic/env.py << 'ENV'
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
ENV

# 5. Vytvorenie __init__.py pre modely
cat > backend/app/models/__init__.py << 'MODELS'
"""Databázové modely."""

from app.core.database import Base
from app.models.base import BaseModel
from app.models.user import User, UserRole, UserStatus
from app.models.company import Company, CompanyType, CompanyStatus
from app.models.listing import Listing, ListingType, ListingCategory, ListingStatus, ListingCondition
from app.models.reservation import Reservation, ReservationStatus
from app.models.membership import Membership, MembershipRole, MembershipStatus
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "UserRole",
    "UserStatus",
    "Company",
    "CompanyType",
    "CompanyStatus",
    "Listing",
    "ListingType",
    "ListingCategory",
    "ListingStatus",
    "ListingCondition",
    "Reservation",
    "ReservationStatus",
    "Membership",
    "MembershipRole",
    "MembershipStatus",
    "AuditLog",
]
MODELS

echo "✅ Importy opravené"
