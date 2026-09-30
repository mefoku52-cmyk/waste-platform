"""Admin-only approvals endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.approval.approval_service import (
    DefaultApprovalService,
)
from app.modules.agent_platform.domain.approval.approval_decision import ApprovalDecision
from app.modules.agent_platform.domain.approval.approval_status import ApprovalStatus
from app.modules.agent_platform.infrastructure.models import ApprovalRequestModel
from app.modules.agent_platform.infrastructure.persistence.approval_repository import (
    SqlAlchemyApprovalRepository,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_admin
from app.shared.presentation.authorization import current_user_id

router = APIRouter(
    prefix="/agent-platform/approvals",
    tags=["agent-platform-approvals"],
)


class DecideRequest(BaseModel):
    reason: str


@router.get("")
async def list_approvals(
    limit: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = select(ApprovalRequestModel).order_by(desc(ApprovalRequestModel.created_at))
    if status:
        stmt = stmt.where(ApprovalRequestModel.status == status)
    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "approvalId": r.approval_id,
                "requestedBy": r.requested_by,
                "requestedByType": r.requested_by_type,
                "action": r.action,
                "target": r.target,
                "reason": r.reason,
                "riskLevel": r.risk_level,
                "status": r.status,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
                "expiresAt": r.expires_at.isoformat() if r.expires_at else None,
                "decidedBy": r.decided_by,
                "decidedAt": r.decided_at.isoformat() if r.decided_at else None,
                "decisionReason": r.decision_reason,
            }
            for r in rows
        ],
        "count": len(rows),
    }


async def _decide(
    approval_id: str,
    target_status: ApprovalStatus,
    reason: str,
    actor: str,
    session: AsyncSession,
) -> dict:
    repo = SqlAlchemyApprovalRepository(session)
    existing = await repo.get(approval_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    svc = DefaultApprovalService(repository=repo)
    decision = ApprovalDecision(
        approval_id=approval_id,
        status=target_status,
        decided_by=actor,
        decided_at=datetime.now(UTC),
        reason=reason or "admin decision",
    )
    result = await svc.decide(decision)
    return {
        "approvalId": result.approval_id,
        "status": result.status.value,
        "decidedBy": result.decided_by,
    }


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: str,
    payload: DecideRequest,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    actor = current_user_id(current_user) or "admin"
    return await _decide(approval_id, ApprovalStatus.APPROVED, payload.reason, actor, session)


@router.post("/{approval_id}/deny")
async def deny(
    approval_id: str,
    payload: DecideRequest,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    actor = current_user_id(current_user) or "admin"
    return await _decide(approval_id, ApprovalStatus.DENIED, payload.reason, actor, session)


@router.get("/{approval_id}/is-executable")
async def is_executable(
    approval_id: str,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Overi, ci approval je schvaleny a neexpirovany."""
    from app.modules.agent_platform.application.approval.approval_workflow import (
        DefaultApprovalWorkflow,
    )

    repo = SqlAlchemyApprovalRepository(session)
    wf = DefaultApprovalWorkflow(repository=repo)
    executable = await wf.is_executable(approval_id)
    return {"approvalId": approval_id, "executable": bool(executable)}
