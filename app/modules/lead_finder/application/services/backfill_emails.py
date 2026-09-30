"""Backfill missing emails for existing outreach candidates.

Pre kazdeho kandidata bez emailu:
  1. Google CSE -> najdi firemny web
  2. Scrape web -> vytiahni email
  3. Uloz do DB

Vracia pocet najdenych.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_finder.application.services.directory_lookup import lookup_public_email
from app.modules.lead_finder.application.services.email_finder import (
    AsyncLegalEmailFinder,
)
from app.modules.lead_finder.application.services.website_finder import WebsiteFinder
from app.modules.lead_finder.infrastructure.persistence.models import (
    OutreachCandidateModel,
)
from app.modules.lead_finder.infrastructure.persistence.repositories import (
    SqlAlchemyOutreachCandidateRepository,
)

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 35


async def backfill_emails(
    session: AsyncSession,
    *,
    limit: int = DEFAULT_LIMIT,
) -> dict:
    """Nájde emaily pre kandidátov, ktorí ich ešte nemajú."""
    cap = max(1, min(int(limit), 100))

    # SELECT kandidati bez emailu
    stmt = (
        select(OutreachCandidateModel)
        .where(OutreachCandidateModel.email.is_(None))
        .where(OutreachCandidateModel.status.in_(("new", "drafted")))
        .order_by(OutreachCandidateModel.created_at.asc())
        .limit(cap)
    )
    rows = (await session.execute(stmt)).scalars().all()

    repo = SqlAlchemyOutreachCandidateRepository(session)
    website_finder = WebsiteFinder()
    email_finder = AsyncLegalEmailFinder()

    found = 0
    no_website = 0
    no_email_on_website = 0
    failed = 0
    items: list[dict] = []

    try:
        for m in rows:
            company_name = m.company_name
            city = m.city
            ico = m.ico

            try:
                website = await website_finder.find_website(
                    company_name=company_name,
                    city=city,
                )
                if not website:
                    directory_email = lookup_public_email(company_name, city, ico)
                    if directory_email:
                        await repo.update_email(candidate_id=m.id, email=directory_email)
                        found += 1
                        items.append(
                            {
                                "company_name": company_name,
                                "ico": ico,
                                "email": directory_email,
                                "reason": "directory",
                            }
                        )
                        continue
                    no_website += 1
                    items.append(
                        {
                            "company_name": company_name,
                            "ico": ico,
                            "email": None,
                            "reason": "no_website",
                        }
                    )
                    continue

                found_email = await email_finder.find_email_for_company(
                    website, company_name=company_name
                )
                if not found_email:
                    no_email_on_website += 1
                    items.append(
                        {
                            "company_name": company_name,
                            "ico": ico,
                            "website": website,
                            "email": None,
                            "reason": "no_email_on_website",
                        }
                    )
                    continue

                await repo.update_email(
                    candidate_id=str(m.id),
                    email=found_email,
                )
                found += 1
                items.append(
                    {
                        "company_name": company_name,
                        "ico": ico,
                        "website": website,
                        "email": found_email,
                        "reason": "found",
                    }
                )
                logger.info("Backfill email: %s -> %s", company_name, found_email)

            except Exception:
                logger.exception("Backfill failed for %s", company_name)
                failed += 1
                items.append(
                    {
                        "company_name": company_name,
                        "ico": ico,
                        "email": None,
                        "reason": "error",
                    }
                )
    finally:
        await email_finder.close()

    return {
        "ok": True,
        "processed": len(rows),
        "found": found,
        "no_website": no_website,
        "no_email_on_website": no_email_on_website,
        "failed": failed,
        "items": items,
    }
