"""Lead finder admin endpoints – draft and send outreach emails.

Platform-admin only. One email per request. No bulk auto-send.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.modules.lead_finder.application.services.email_drafter import (
    EmailDrafter,
)
from app.shared.application.side_effects import write_audit
from app.shared.infrastructure.db.session import get_db_session
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


@router.post("/draft", response_model=DraftResponse)
async def draft_email(
    payload: DraftRequest,
    current_user=Depends(require_current_user),
) -> DraftResponse:
    _require_admin(current_user)
    try:
        draft = await EmailDrafter().draft(
            company_name=payload.company_name,
            city=payload.city,
            industry=payload.industry,
            reason=payload.reason,
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

    ok = send_email(to=payload.to, subject=payload.subject, body=payload.body)

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="lead_outreach.send",
        target_type="email",
        target_id=payload.to,
        details=f"subject={payload.subject[:80]}",
    )

    if not ok:
        return SendResponse(
            ok=False,
            message="SMTP nie je nakonfigurované alebo odoslanie zlyhalo.",
        )
    return SendResponse(ok=True, message="Email odoslaný.")
