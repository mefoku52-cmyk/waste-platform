import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force using settings - ignore DATABASE_URL env var
# Use settings from config.py
from app.core.config import settings

# Build URL from settings
DATABASE_URL = settings.database.async_url

engine = create_async_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
