"""In-process scheduler (APScheduler) for daily background jobs."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _daily_lead_discover_wrapper() -> None:
    """Draft 30 new RPO companies. Never sends."""
    from app.modules.lead_finder.application.services.daily_discover import (
        run_daily_discover,
    )
    from app.shared.infrastructure.db.session import async_session_factory

    try:
        async with async_session_factory() as session:
            result = await run_daily_discover(session)
            logger.info("Daily lead discover result: %s", result)
    except Exception:
        logger.exception("Daily lead discover zlyhal")


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


async def run_lead_discover_job() -> None:
    from app.modules.lead_finder.application.services.daily_discover import (
        run_daily_discover,
    )
    from app.shared.infrastructure.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await run_daily_discover(session, draft=False)


def start_scheduler() -> AsyncIOScheduler | None:
    """Start APScheduler with daily matching job. Idempotent."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    matching_on = bool(getattr(settings, "MATCHING_ENABLED", False))
    outreach_on = bool(getattr(settings, "LEAD_OUTREACH_ENABLED", False))
    if not matching_on and not outreach_on:
        logger.info("scheduler off – matching aj outreach vypnute")
        return None

    scheduler = AsyncIOScheduler(timezone="Europe/Bratislava")
    if matching_on:
        scheduler.add_job(
            _daily_matching_wrapper,
            CronTrigger(hour=settings.MATCHING_HOUR, minute=settings.MATCHING_MINUTE),
            id="daily_matching",
            replace_existing=True,
            misfire_grace_time=3600,
        )
    if outreach_on:
        scheduler.add_job(
            _daily_lead_discover_wrapper,
            CronTrigger(hour=7, minute=15),
            id="daily_lead_discover",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    scheduler.add_job(
        run_lead_discover_job,
        "interval",
        hours=12,
        id="lead_discover_12h",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Scheduler started matching=%s outreach=%s",
        matching_on,
        outreach_on,
    )
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
