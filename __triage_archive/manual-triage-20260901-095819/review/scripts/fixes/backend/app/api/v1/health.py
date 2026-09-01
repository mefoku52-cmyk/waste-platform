
"""Health check endpointy."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis

from app.core.database import get_db
from app.core.config import settings
from app.core.metrics import metrics_endpoint

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
        # Kontrola databázy
        await db.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        db_ok = False
    
    try:
        # Kontrola Redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    
    return {
        "status": "ready" if db_ok and redis_ok else "not_ready",
        "database": db_ok,
        "redis": redis_ok,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/live")
async def liveness_check() -> dict:
    """Kontrola živosti aplikácie."""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metriky."""
    return await metrics_endpoint()
