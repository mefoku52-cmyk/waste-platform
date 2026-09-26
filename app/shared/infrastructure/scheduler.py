"""In-process scheduler (APScheduler) for daily background jobs."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _daily_matching_wrapper() -> None:
    """Run the daily matching job in its own DB session."""
    from app.modules.recommendations.application.matching_job import run_daily_matching
    from app.shared.infrastructure.db.session import async_session_factory

    try:
        async with async_session_factory() as session:
            result = await run_daily_matching(session)
            logger.info("Daily matching result: %s", result)
    except Exception:
        logger.exception("Daily matching job zlyhal")


def start_scheduler() -> AsyncIOScheduler | None:
    """Start APScheduler with daily matching job. Idempotent."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    if not settings.MATCHING_ENABLED:
        logger.info("MATCHING_ENABLED=false – scheduler sa nespustí")
        return None

    scheduler = AsyncIOScheduler(timezone="Europe/Bratislava")
    scheduler.add_job(
        _daily_matching_wrapper,
        CronTrigger(hour=settings.MATCHING_HOUR, minute=settings.MATCHING_MINUTE),
        id="daily_matching",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Scheduler started – daily matching at %02d:%02d",
        settings.MATCHING_HOUR,
        settings.MATCHING_MINUTE,
    )
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
