"""Database session provider."""

from app.shared.infrastructure.db.session import SessionLocal, async_engine
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session() -> AsyncSession:
    """Yield async DB session for dependency injection."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
