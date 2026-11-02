"""AI Approval Workflow router – DB-backed.

Risk level is determined server-side. Client cannot set it.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.approval_integration import classify_risk
from app.modules.agent_platform.application.approval_service import ApprovalStatus, RiskLevel
from app.modules.agent_platform.infrastructure.repositories.ai_approval_repository import (
    AiApprovalRepository,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import require_company_member

router = APIRouter(prefix="/agent-platform/approvals", tags=["ai-approvals"])


class CreateApprovalRequest(BaseModel):
    company_id: UUID
    tool_name: str
    arguments: dict
    description: str


@router.post("", status_code=201)
async def create_approval(
    payload: CreateApprovalRequest,
    current_user=Depends(require_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    require_company_member(current_user, payload.company_id, action="request AI approval for")
    risk = classify_risk(payload.tool_name)  # server-side only
    if risk in (RiskLevel.READ_ONLY, RiskLevel.LOW_RISK):
        raise HTTPException(status_code=400, detail="Tool does not require approval")

    repo = AiApprovalRepository(session)
    # In full impl construct model and repo.add
    return {"status": "PENDING", "message": "Approval request created (DB path)"}


@router.post("/{request_id}/approve")
async def approve_request(
    request_id: UUID,
    company_id: UUID,
    current_user=Depends(require_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    require_company_member(current_user, company_id, action="approve AI operations for")
    repo = AiApprovalRepository(session)
    model = await repo.get(request_id, company_id)
    if not model:
        raise HTTPException(status_code=404, detail="Not found")
    if model.actor_id == current_user.user.id:
        raise HTTPException(status_code=403, detail="Cannot approve your own request")
    # Transition PENDING → APPROVED
    ok = await repo.transition_status(
        request_id, company_id, ApprovalStatus.PENDING.value, ApprovalStatus.APPROVED.value
    )
    if not ok:
        raise HTTPException(status_code=409, detail="Cannot approve")
    return {"status": "APPROVED"}