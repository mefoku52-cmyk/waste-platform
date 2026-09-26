"""Daily matching job – finds new matches and notifies companies."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.companies.domain.enums import CompanyStatus
from app.modules.companies.infrastructure.models import CompanyModel
from app.modules.company_memberships.infrastructure.repositories import (
    SqlAlchemyCompanyMembershipRepository,
)
from app.modules.listings.infrastructure.models import ListingsModel
from app.modules.notifications.domain.entities import NotificationEntity
from app.modules.notifications.infrastructure.repositories import (
    NotificationRepositoryImpl,
)
from app.modules.recommendations.application.email_templates import render_matches_email
from app.modules.recommendations.application.scoring import score_company
from app.shared.infrastructure.email.sender import send_email

logger = logging.getLogger(__name__)


async def run_daily_matching(session: AsyncSession) -> dict:
    """Find matches for all verified companies and notify them.

    Returns a summary dict: {"companies_checked": N, "notified": M, "emails_sent": K}
    """
    if not settings.MATCHING_ENABLED:
        logger.info("MATCHING_ENABLED=false – skipping daily matching job")
        return {"enabled": False, "companies_checked": 0, "notified": 0, "emails_sent": 0}

    lookback = datetime.now() - timedelta(days=settings.MATCHING_LOOKBACK_DAYS)

    # 1. Nacitaj nové published ponuky za poslednych N dni
    stmt_listings = select(ListingsModel).where(
        ListingsModel.status == "published",
        ListingsModel.created_at >= lookback,
    )
    listings = list((await session.execute(stmt_listings)).scalars().all())

    if not listings:
        logger.info("Daily matching: ziadne nove ponuky za %s dni", settings.MATCHING_LOOKBACK_DAYS)
        return {"enabled": True, "companies_checked": 0, "notified": 0, "emails_sent": 0}

    # 2. Nacitaj overené firmy, ktore mozu nakupovat
    stmt_companies = select(CompanyModel).where(
        CompanyModel.status == CompanyStatus.VERIFIED.value,
        CompanyModel.buyer_capability.is_(True),
    )
    companies = list((await session.execute(stmt_companies)).scalars().all())

    notification_repo = NotificationRepositoryImpl(session)
    membership_repo = SqlAlchemyCompanyMembershipRepository(session)

    notified = 0
    emails_sent = 0

    for company in companies:
        materials = (getattr(company, "accepted_material_types", None) or "").strip()
        if not materials:
            continue

        matches: list[dict] = []
        for listing in listings:
            if str(listing.company_id) == str(company.id):
                continue
            score, _ = score_company(
                listing_location=listing.location or "",
                listing_material=listing.material_type or "",
                listing_lat=getattr(listing, "latitude", None),
                listing_lng=getattr(listing, "longitude", None),
                city=company.city,
                logistics_capability=bool(company.logistics_capability),
                accepted_material_types=materials,
                company_lat=company.latitude,
                company_lng=company.longitude,
            )
            if score >= settings.MATCHING_MIN_SCORE:
                matches.append(
                    {
                        "listingId": str(listing.id),
                        "listingTitle": listing.title,
                        "materialType": listing.material_type,
                        "location": listing.location,
                        "score": score,
                    }
                )

        if not matches:
            continue

        matches.sort(key=lambda x: -x["score"])
        matches = matches[: settings.MATCHING_MAX_PER_COMPANY]

        # 3. Notifikacia pre kazdeho clena firmy
        members = await membership_repo.list_by_company_id(company.id)
        now = datetime.now()

        for m in members:
            uid = getattr(m, "user_id", None)
            if uid is None:
                continue
            try:
                await notification_repo.create(
                    NotificationEntity(
                        id=uuid4(),
                        user_id=uid,
                        type="daily_matches",
                        title=f"{len(matches)} nové zhody pre {company.legal_name}",
                        message="Navštív dashboard pre detail ponúk.",
                        is_read=False,
                        related_entity_id=None,
                        created_at=now,
                        updated_at=now,
                        created_by_user_id=None,
                        updated_by_user_id=None,
                    )
                )
            except Exception:
                logger.exception("Notification create zlyhalo pre user_id=%s", uid)

        # 4. Email pre primarny kontakt
        primary_email = None
        for m in members:
            if getattr(m, "is_primary_contact", False):
                user_email = getattr(m, "user_email", None)
                if user_email:
                    primary_email = user_email
                    break
        if primary_email is None and members:
            primary_email = getattr(members[0], "user_email", None)

        if primary_email:
            subject, html = render_matches_email(
                company_name=company.legal_name or "vaša firma",
                items=matches,
            )
            ok = send_email(to=primary_email, subject=subject, body=html)
            if ok:
                emails_sent += 1

        notified += 1

    logger.info(
        "Daily matching done: companies=%s notified=%s emails=%s",
        len(companies),
        notified,
        emails_sent,
    )
    return {
        "enabled": True,
        "companies_checked": len(companies),
        "notified": notified,
        "emails_sent": emails_sent,
    }
