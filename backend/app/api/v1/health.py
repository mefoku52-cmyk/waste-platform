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
