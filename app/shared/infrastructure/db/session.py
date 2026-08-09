import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_env_database_url = os.getenv("DATABASE_URL")

if _env_database_url:
    if _env_database_url.startswith("sqlite") and not _env_database_url.startswith("sqlite+aiosqlite"):
        DATABASE_URL = _env_database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    else:
        DATABASE_URL = _env_database_url
else:
    DATABASE_URL = settings.database.async_url

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    connect_args=_connect_args,
)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
