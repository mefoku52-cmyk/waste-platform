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
