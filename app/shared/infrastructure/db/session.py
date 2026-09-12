from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _db_url() -> str:
    db = getattr(settings, "database", None)
    for attr in ("async_url", "url"):
        if db is not None:
            val = getattr(db, attr, None)
            if val:
                return str(val)
    return str(getattr(settings, "DATABASE_URL", "sqlite+aiosqlite:///./var/cmep.db"))


DATABASE_URL = _db_url()
ASYNC_DATABASE_URL = DATABASE_URL
SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=bool(getattr(getattr(settings, "database", None), "echo", False)),
    pool_pre_ping=True,
    connect_args=connect_args,
)

async_engine = engine

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

AsyncSessionLocal = async_session_maker
async_session_factory = async_session_maker
SessionLocal = async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


get_session = get_db_session
get_db = get_db_session


async def dispose_engine() -> None:
    await engine.dispose()


dispose = dispose_engine
close_engine = dispose_engine


async def get_engine() -> AsyncEngine:
    return engine


get_async_session = get_db_session
