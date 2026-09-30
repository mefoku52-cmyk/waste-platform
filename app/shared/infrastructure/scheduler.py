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


async def _cleanup_pending_users_wrapper() -> None:
    """Zmaze userov v stave pending_verification starsich ako 7 dni.

    Bez tohto jobu sa DB plni zombie uctami z fake registracii.
    """
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import delete, select

    from app.modules.users.infrastructure.models import UserModel
    from app.shared.infrastructure.db.session import async_session_factory

    days = int(getattr(settings, "CLEANUP_PENDING_USERS_DAYS", 7))
    cutoff = datetime.now(UTC) - timedelta(days=days)
    try:
        async with async_session_factory() as session:
            stmt = select(UserModel.id).where(
                UserModel.status == "pending_verification",
                UserModel.created_at < cutoff,
            )
            result = await session.execute(stmt)
            ids = [row[0] for row in result.all()]
            if not ids:
                logger.info("Cleanup pending users: nothing to delete")
                return
            await session.execute(delete(UserModel).where(UserModel.id.in_(ids)))
            await session.commit()
            logger.info("Cleanup pending users: deleted %d stale accounts", len(ids))
    except Exception:
        logger.exception("Cleanup pending users zlyhal")


async def _daily_lead_outreach_wrapper() -> None:
    """Daily outreach — najdi 35 novych firiem + draftni emaily.

    Spusti sa denne o 9:00 Europe/Bratislava. 30 z RPO + 5 z backfillu.
    """
    from app.modules.lead_finder.application.services.backfill_emails import (
        backfill_emails,
    )
    from app.modules.lead_finder.application.services.daily_discover import (
        run_daily_discover,
    )
    from app.shared.infrastructure.db.session import async_session_factory

    try:
        async with async_session_factory() as session:
            # 1. Najdi 30 novych firiem z RPO + draftni
            result = await run_daily_discover(session, limit=30, draft=True)
            logger.info(
                "Daily lead discover: %s",
                {
                    "picked": (result or {}).get("picked"),
                    "created": (result or {}).get("created"),
                    "drafted": (result or {}).get("drafted"),
                    "emails_found": (result or {}).get("emails_found"),
                },
            )

        # 2. Backfill emaily pre starych bez emailu (5 firiem)
        async with async_session_factory() as session:
            bf = await backfill_emails(session, limit=5)
            logger.info(
                "Daily backfill emails: %s",
                {
                    "processed": bf.get("processed"),
                    "found": bf.get("found"),
                },
            )
    except Exception:
        logger.exception("Daily lead outreach zlyhal")


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
        await run_daily_discover(session, draft=True)


def start_scheduler() -> AsyncIOScheduler | None:
    """Start APScheduler with daily matching job. Idempotent."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    matching_on = bool(getattr(settings, "MATCHING_ENABLED", False))
    outreach_on = bool(getattr(settings, "LEAD_OUTREACH_ENABLED", False))
    cleanup_on = bool(getattr(settings, "CLEANUP_PENDING_USERS_ENABLED", True))
    if not matching_on and not outreach_on and not cleanup_on:
        logger.info("scheduler off – matching, outreach aj cleanup vypnute")
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
    if cleanup_on:
        scheduler.add_job(
            _cleanup_pending_users_wrapper,
            CronTrigger(hour=4, minute=0),
            id="cleanup_pending_users",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    scheduler.add_job(
        _daily_lead_outreach_wrapper,
        CronTrigger(hour=9, minute=0),
        id="daily_lead_outreach",
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
        "Scheduler started matching=%s outreach=%s cleanup=%s",
        matching_on,
        outreach_on,
        cleanup_on,
    )
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
