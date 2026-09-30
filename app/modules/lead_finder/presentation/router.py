"""Lead finder admin endpoints – draft and send outreach emails.

Platform-admin only. One email per request. No bulk auto-send.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.modules.lead_finder.application.services.batch_drafter import (
    BatchDrafter,
    CompanyInput,
)
from app.modules.lead_finder.application.services.email_drafter import (
    EmailDrafter,
)
from app.shared.application.side_effects import write_audit
from app.shared.infrastructure.db.session import get_db_session
from app.shared.infrastructure.email.resend_sender import send_via_resend
from app.shared.infrastructure.email.sender import send_email
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_platform_admin,
)

router = APIRouter(prefix="/admin/lead-outreach", tags=["admin-lead-outreach"])


class DraftRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    industry: str | None = Field(default=None, max_length=128)
    reason: str | None = Field(default=None, max_length=500)


class DraftResponse(BaseModel):
    subject: str
    body: str


class SendRequest(BaseModel):
    to: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=20000)


class SendResponse(BaseModel):
    ok: bool
    message: str


def _require_admin(current_user) -> None:
    if not is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Platform admin access required")


class BatchCompanyItem(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    industry: str | None = Field(default=None, max_length=128)
    reason: str | None = Field(default=None, max_length=500)


class BatchDraftRequest(BaseModel):
    companies: list[BatchCompanyItem] = Field(min_length=1, max_length=30)


class BatchDraftItem(BaseModel):
    company_name: str
    city: str | None
    industry: str | None
    subject: str
    body: str


class BatchDraftResponse(BaseModel):
    count: int
    items: list[BatchDraftItem]


EARLY_BIRD_LIMIT = 10


class DiscoverDailyItem(BaseModel):
    id: str
    company_name: str
    ico: str | None = None
    city: str | None = None
    industry: str | None = None
    subject: str | None = None
    body: str | None = None
    email: str | None = None


class DiscoverDailyResponse(BaseModel):
    ok: bool
    picked: int
    created: int
    drafted: int
    failed: int
    emails_found: int = 0
    known_before: int
    send: bool = False
    items: list[DiscoverDailyItem] = []


@router.post("/discover-daily", response_model=DiscoverDailyResponse)
async def discover_daily(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    _require_admin(current_user)
    from app.modules.lead_finder.application.services.daily_discover import (
        run_daily_discover,
    )

    result = await run_daily_discover(session, draft=False)
    return DiscoverDailyResponse(**result)


@router.post("/draft", response_model=DraftResponse)
async def draft_email(
    payload: DraftRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> DraftResponse:
    _require_admin(current_user)

    # Zisti, kolko overenych firiem je na platforme.
    early_bird = False
    try:
        r = await session.execute(text("SELECT COUNT(*) FROM companies WHERE status = 'verified'"))
        verified_count = int(r.scalar() or 0)
        early_bird = verified_count < EARLY_BIRD_LIMIT
    except Exception:
        early_bird = False

    try:
        draft = await EmailDrafter().draft(
            company_name=payload.company_name,
            city=payload.city,
            industry=payload.industry,
            reason=payload.reason,
            early_bird=early_bird,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Nepodarilo sa pripraviť návrh emailu.",
        )
    return DraftResponse(subject=draft.subject, body=draft.body)


@router.post("/send", response_model=SendResponse)
async def send_outreach_email(
    payload: SendRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> SendResponse:
    _require_admin(current_user)

    result = await send_via_resend(
        session=session,
        to=payload.to,
        subject=payload.subject,
        body=payload.body,
    )

    if not result.ok:
        # Fallback na SMTP len ak Resend nie je nakonfigurovany vobec
        if "nie je nakonfigurovany" in result.message:
            ok = send_email(to=payload.to, subject=payload.subject, body=payload.body)
            if ok:
                await write_audit(
                    session=session,
                    actor_user_id=current_user_id(current_user),
                    action="lead_outreach.send",
                    target_type="email",
                    target_id=payload.to,
                    details=f"via=smtp,subject={payload.subject[:80]}",
                )
                return SendResponse(ok=True, message="Email odoslaný cez SMTP.")
            return SendResponse(ok=False, message="SMTP zlyhalo.")
        return SendResponse(ok=False, message=result.message)

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="lead_outreach.send",
        target_type="email",
        target_id=payload.to,
        details=f"via=resend,subject={payload.subject[:80]}",
    )

    remaining = result.remaining_today
    msg = result.message
    if remaining is not None:
        msg = f"{msg} Zostáva dnes: {remaining}."
    return SendResponse(ok=True, message=msg)


@router.post("/draft-batch", response_model=BatchDraftResponse)
async def draft_batch(
    payload: BatchDraftRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> BatchDraftResponse:
    """Draft N emails at once (max 30). Admin only."""
    _require_admin(current_user)

    # Early bird detection (rovnaka logika ako v /draft)
    early_bird = False
    try:
        r = await session.execute(text("SELECT COUNT(*) FROM companies WHERE status = 'verified'"))
        verified_count = int(r.scalar() or 0)
        early_bird = verified_count < EARLY_BIRD_LIMIT
    except Exception:
        early_bird = False

    companies = [
        CompanyInput(
            company_name=c.company_name,
            city=c.city,
            industry=c.industry,
            reason=c.reason,
        )
        for c in payload.companies
    ]

    try:
        items = await BatchDrafter().draft_batch(
            companies=companies,
            early_bird=early_bird,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Nepodarilo sa pripraviť dávku emailov.",
        )

    return BatchDraftResponse(
        count=len(items),
        items=[
            BatchDraftItem(
                company_name=i.company_name,
                city=i.city,
                industry=i.industry,
                subject=i.subject,
                body=i.body,
            )
            for i in items
        ],
    )


# ══════════════════════════════════════════════════════════════
# PENDING / SEND / SKIP  — automaticky outreach workflow
# ══════════════════════════════════════════════════════════════


class PendingCandidateItem(BaseModel):
    id: str
    company_name: str
    ico: str | None = None
    city: str | None = None
    industry: str | None = None
    email: str | None = None
    subject: str | None = None
    body: str | None = None
    status: str
    created_at: str | None = None


class PendingCandidatesResponse(BaseModel):
    count: int
    items: list[PendingCandidateItem]


class SendCandidateRequest(BaseModel):
    to: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=20000)


class SendCandidateResponse(BaseModel):
    ok: bool
    message: str
    status: str = "sent"


class BackfillEmailsItem(BaseModel):
    company_name: str
    ico: str | None = None
    website: str | None = None
    email: str | None = None
    reason: str


class BackfillEmailsResponse(BaseModel):
    ok: bool
    processed: int
    found: int
    no_website: int
    no_email_on_website: int
    failed: int
    items: list[BackfillEmailsItem] = []


@router.post("/backfill-emails", response_model=BackfillEmailsResponse)
async def backfill_emails_endpoint(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
    limit: int = 35,
) -> BackfillEmailsResponse:
    """Najde emaily pre existujucich kandidatov, ktori ich nemaju.

    Google CSE -> firemny web -> scrape email -> uloz.
    Limit max 100, default 35.
    """
    _require_admin(current_user)

    from app.modules.lead_finder.application.services.backfill_emails import (
        backfill_emails,
    )

    result = await backfill_emails(session, limit=limit)
    return BackfillEmailsResponse(**result)


@router.get("/pending", response_model=PendingCandidatesResponse)
async def list_pending_candidates(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
    limit: int = 50,
):
    """Vrati vsetkych kandidatov so statusom drafted, ktori cakaju na odoslanie."""
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)
    rows = await repo.list_by_status(
        status=OutreachStatus.DRAFTED,
        limit=limit,
    )

    items = [
        PendingCandidateItem(
            id=r.id,
            company_name=r.company_name,
            ico=r.ico,
            city=r.city,
            industry=r.industry,
            email=r.email,
            subject=r.draft_subject,
            body=r.draft_body,
            status=r.status.value,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]

    return PendingCandidatesResponse(count=len(items), items=items)


@router.post("/candidates/{candidate_id}/send", response_model=SendCandidateResponse)
async def send_candidate_email(
    candidate_id: str,
    payload: SendCandidateRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> SendCandidateResponse:
    """Odesle jeden pripraveny email a oznaci kandidata ako 'sent'."""
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)
    candidate = await repo.get_by_id(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Kandidat sa nenasiel")

    result = await send_via_resend(
        session=session,
        to=payload.to,
        subject=payload.subject,
        body=payload.body,
    )

    if not result.ok:
        if "nie je nakonfigurovany" in result.message:
            ok = send_email(to=payload.to, subject=payload.subject, body=payload.body)
            if not ok:
                return SendCandidateResponse(ok=False, message="SMTP zlyhalo.")
        else:
            return SendCandidateResponse(ok=False, message=result.message)

    await repo.update_status(
        candidate_id=candidate_id,
        status=OutreachStatus.SENT,
    )

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="lead_outreach.send_candidate",
        target_type="outreach_candidate",
        target_id=candidate_id,
        details=f"to={payload.to},company={candidate.company_name}",
    )

    remaining = getattr(result, "remaining_today", None)
    msg = result.message if result.ok else "Email odoslaný cez SMTP."
    if remaining is not None:
        msg = f"{msg} Zostáva dnes: {remaining}."

    return SendCandidateResponse(ok=True, message=msg, status="sent")


class SkipCandidateResponse(BaseModel):
    ok: bool
    status: str


@router.post("/candidates/{candidate_id}/skip", response_model=SkipCandidateResponse)
async def skip_candidate(
    candidate_id: str,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> SkipCandidateResponse:
    """Preskoci kandidata (status -> skipped)."""
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)
    candidate = await repo.get_by_id(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Kandidat sa nenasiel")

    await repo.update_status(
        candidate_id=candidate_id,
        status=OutreachStatus.SKIPPED,
    )
    return SkipCandidateResponse(ok=True, status="skipped")
