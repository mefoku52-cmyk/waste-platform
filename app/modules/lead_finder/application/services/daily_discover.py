"""Pick 30 new Slovak companies from official RPO and draft emails.

Never sends. Skips ICO already stored. RPO has no email.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.application.rpo import search_rpo
from app.modules.lead_finder.application.services.email_drafter import EmailDrafter
from app.modules.lead_finder.application.services.email_finder import LegalEmailFinder
from app.modules.lead_finder.application.services.website_finder import WebsiteFinder
from app.modules.lead_finder.infrastructure.persistence.models import (
    OutreachCandidateModel,
)
from app.modules.lead_finder.infrastructure.persistence.repositories import (
    SqlAlchemyOutreachCandidateRepository,
)

logger = logging.getLogger(__name__)

MAX_DAILY = 30
SKIP_MARKERS = ("konkurz", "likvidac", "vzniku")
QUERIES: tuple[dict[str, str], ...] = (
    {"full_name": "recykl"},
    {"full_name": "odpady"},
    {"full_name": "drevo"},
    {"full_name": "plasty"},
    {"full_name": "kovosrot"},
    {"full_name": "papier"},
    {"full_name": "sklo"},
    {"full_name": "textil"},
    {"full_name": "kompost"},
    {"full_name": "zberna"},
    {"municipality": "Presov", "main_activity": "odpad"},
    {"municipality": "Kosice", "main_activity": "recykl"},
    {"municipality": "Zilina", "main_activity": "drevo"},
    {"municipality": "Bratislava", "main_activity": "odpad"},
)


def _usable(row: dict[str, Any], known: set[str]) -> bool:
    name = str(row.get("legalName") or "").strip()
    ico = str(row.get("ico") or "").strip()
    if not name or len(ico) != 8:
        return False
    if ico in known:
        return False
    low = name.lower()
    return not any(m in low for m in SKIP_MARKERS)


async def run_daily_discover(
    session: AsyncSession,
    *,
    limit: int = MAX_DAILY,
    draft: bool = False,
) -> dict[str, Any] | None:
    cap = max(1, min(int(limit), MAX_DAILY))
    repo = SqlAlchemyOutreachCandidateRepository(session)
    existing = await session.execute(
        select(OutreachCandidateModel.ico).where(OutreachCandidateModel.ico.is_not(None))
    )
    known = {str(v).strip() for v in existing.scalars().all() if v}
    from datetime import datetime

    slot = int(datetime.now(UTC).timestamp() // 43200)
    rotated = QUERIES[slot % len(QUERIES) :] + QUERIES[: slot % len(QUERIES)]
    picked: list[dict[str, Any]] = []
    for query in rotated:
        if len(picked) >= cap:
            break
        try:
            rows = search_rpo(limit=10, only_active=True, **query)
        except Exception:
            logger.exception("rpo search failed %s", query)
            continue
        for row in rows:
            if not _usable(row, known):
                continue
            ico = str(row["ico"])
            known.add(ico)
            picked.append(row)
            if len(picked) >= cap:
                break

    drafter = EmailDrafter()
    website_finder = WebsiteFinder()
    email_finder = LegalEmailFinder()
    created = 0
    drafted = 0
    failed = 0
    emails_found = 0
    items: list[dict[str, Any]] = []

    try:
        for row in picked:
            try:
                candidate = await repo.create(
                    company_name=str(row["legalName"]),
                    ico=str(row["ico"]),
                    city=row.get("city"),
                    industry=row.get("activity") or "obehove materialy",
                    email=None,
                )
                created += 1
            except Exception:
                logger.exception("create candidate failed %s", row.get("ico"))
                failed += 1
                continue

            # --- Email discovery: Google search -> web -> scrape email ---
            found_email: str | None = None
            try:
                website = await website_finder.find_website(
                    company_name=candidate.company_name,
                    city=candidate.city,
                )
                if website:
                    found_email = await asyncio.to_thread(
                        email_finder.find_email_for_company, website
                    )
                    if found_email:
                        await repo.update_email(
                            candidate_id=candidate.id,
                            email=found_email,
                        )
                        emails_found += 1
                        logger.info(
                            "Email found for %s (%s): %s",
                            candidate.company_name,
                            candidate.ico,
                            found_email,
                        )
            except Exception:
                logger.exception("email discovery failed for %s", candidate.company_name)

            item = {
                "id": candidate.id,
                "company_name": candidate.company_name,
                "ico": candidate.ico,
                "city": candidate.city,
                "industry": candidate.industry,
                "subject": None,
                "body": None,
                "email": found_email,
            }
            if draft:
                try:
                    mail = await drafter.draft(
                        company_name=candidate.company_name,
                        city=candidate.city,
                        industry=candidate.industry,
                        reason="platforma na obehove materialy a druhotny odpad",
                        early_bird=False,
                    )
                    await repo.update_draft(
                        candidate_id=candidate.id,
                        subject=mail.subject,
                        body=mail.body,
                    )
                    drafted += 1
                    item["subject"] = mail.subject
                    item["body"] = mail.body
                except Exception:
                    logger.exception("draft failed %s", candidate.ico)
                    failed += 1
            items.append(item)
    finally:
        email_finder.close()

    return {
        "ok": True,
        "picked": len(picked),
        "created": created,
        "drafted": drafted,
        "failed": failed,
        "emails_found": emails_found,
        "known_before": len(known) - len(picked),
        "send": False,
        "items": items,
    }
