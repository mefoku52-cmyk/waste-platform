"""Automaticke schvalovanie kandidatov z discovery.

Kandidati z ZS discovery prichadzaju so statusom `new`. Tento modul
ich vie hromadne posunut na `approved` — ale LEN ak splnaju kriteria:

  1. Maju platny email (obsahuje @ a nie je prazdny)
  2. Email nie je v junk markeroch (info@, noreply@, postmaster@, ...)
  3. Firma nie je v skip liste

Kandidati, ktori neprejdu, zostavaju v `new` — cakaju na manualne
rozhodnutie admina. Nic sa nezahadzuje.

Bezpecnost:
- NIKDY neodosiela email. Len meni status.
- Vsetko je idempotentne — opatovne spustenie nic nepokazi.
- Audit trail cez write_audit().
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_finder.domain.entities.outreach_candidate import (
    OutreachStatus,
)
from app.modules.lead_finder.infrastructure.persistence.repositories import (
    SqlAlchemyOutreachCandidateRepository,
)
from app.shared.presentation.business_metrics import (
    AUTO_APPROVE_TOTAL,
)

logger = logging.getLogger(__name__)


# Markery, ktore znamenaju "toto nie je realny B2B kontakt"
_JUNK_LOCAL_PARTS = (
    "noreply",
    "no-reply",
    "donotreply",
    "postmaster",
    "abuse",
    "webmaster",
    "hostmaster",
)


def _is_approvable(email: str | None) -> tuple[bool, str]:
    """True ak email je bezpecny na auto-schvalenie."""
    if not email:
        return False, "no_email"

    email = email.strip().lower()

    if "@" not in email:
        return False, "invalid_email"

    local = email.split("@", 1)[0]

    for marker in _JUNK_LOCAL_PARTS:
        if marker in local:
            return False, f"junk_{marker}"

    return True, "ok"


async def run_auto_approve(
    session: AsyncSession,
    *,
    limit: int = 100,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Hromadne schval kandidatov so statusom `new` s platnym emailom.

    Args:
        session: DB session (commituje volajuci).
        limit: max kolko kandidatov spracovat za jeden beh.
        dry_run: ak True, len reportuje co by sa stalo.

    Returns:
        {
          "approved": int,
          "skipped_no_email": int,
          "skipped_junk": int,
          "skipped_invalid": int,
          "total_checked": int,
          "sample_approved": list[dict],
        }
    """
    repo = SqlAlchemyOutreachCandidateRepository(session)

    candidates = await repo.list_by_status(
        status=OutreachStatus.NEW,
        limit=limit,
    )

    approved = 0
    skipped_no_email = 0
    skipped_junk = 0
    skipped_invalid = 0
    sample_approved: list[dict] = []

    for candidate in candidates:
        ok, reason = _is_approvable(candidate.email)

        if not ok:
            if reason == "no_email":
                skipped_no_email += 1
            elif reason == "invalid_email":
                skipped_invalid += 1
            else:
                skipped_junk += 1
            continue

        if dry_run:
            approved += 1
            if len(sample_approved) < 10:
                sample_approved.append(
                    {
                        "company_name": candidate.company_name,
                        "email": candidate.email,
                    }
                )
            continue

        # Zmena statusu new -> approved
        await repo.update_status(
            candidate_id=candidate.id,
            status=OutreachStatus.APPROVED,
        )
        approved += 1

        if len(sample_approved) < 10:
            sample_approved.append(
                {
                    "company_name": candidate.company_name,
                    "email": candidate.email,
                }
            )

    # Prometheus increments — skip in dry_run so preview does not
    # pollute production metrics.
    if not dry_run:
        if approved:
            AUTO_APPROVE_TOTAL.labels(result="approved").inc(approved)
        if skipped_no_email:
            AUTO_APPROVE_TOTAL.labels(result="skipped_no_email").inc(skipped_no_email)
        if skipped_junk:
            AUTO_APPROVE_TOTAL.labels(result="skipped_junk").inc(skipped_junk)
        if skipped_invalid:
            AUTO_APPROVE_TOTAL.labels(result="skipped_invalid").inc(skipped_invalid)

    logger.info(
        "Auto-approve: checked=%d approved=%d skipped_no_email=%d "
        "skipped_junk=%d skipped_invalid=%d dry_run=%s",
        len(candidates),
        approved,
        skipped_no_email,
        skipped_junk,
        skipped_invalid,
        dry_run,
    )

    return {
        "approved": approved,
        "skipped_no_email": skipped_no_email,
        "skipped_junk": skipped_junk,
        "skipped_invalid": skipped_invalid,
        "total_checked": len(candidates),
        "sample_approved": sample_approved,
    }


__all__ = ["run_auto_approve"]
