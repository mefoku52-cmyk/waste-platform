from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _database_url() -> str:
    database = getattr(settings, "database", None)

    if database is not None:
        url = getattr(database, "async_url", None) or getattr(database, "url", None)
    else:
        url = getattr(settings, "DATABASE_URL", None)

    url = str(url or "").strip()

    if not url or "{" in url or "}" in url or "POSTGRES_" in url:
        url = "sqlite+aiosqlite:///./var/cmep.db"

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    if url.startswith("sqlite:///") and not url.startswith("sqlite+aiosqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    return url


DATABASE_URL = _database_url()

if DATABASE_URL.startswith("sqlite"):
    Path("./var").mkdir(parents=True, exist_ok=True)
    engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        echo=bool(getattr(settings.database, "echo", False)),
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=bool(getattr(settings.database, "echo", False)),
        pool_pre_ping=bool(getattr(settings.database, "pool_pre_ping", True)),
    )

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

AsyncSessionLocal = async_session_maker
SessionLocal = async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    await engine.dispose()
