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
