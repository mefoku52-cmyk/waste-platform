"""AI Approval Workflow router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.modules.agent_platform.application.approval_service import (
    ApprovalRequest,
    RiskLevel,
    approval_service,
)
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import require_company_member

router = APIRouter(prefix="/agent-platform/approvals", tags=["ai-approvals"])


class CreateApprovalRequest(BaseModel):
    company_id: UUID
    tool_name: str
    arguments: dict
    description: str
    risk_level: RiskLevel = RiskLevel.MEDIUM_RISK


@router.post("", response_model=ApprovalRequest, status_code=201)
async def create_approval(
    payload: CreateApprovalRequest,
    current_user=Depends(require_current_user),
):
    require_company_member(current_user, payload.company_id, action="request AI approval for")
    actor_id = current_user.user.id
    return approval_service.create(
        actor_id=actor_id,
        company_id=payload.company_id,
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        description=payload.description,
        risk_level=payload.risk_level,
    )


@router.get("/{request_id}", response_model=ApprovalRequest)
async def get_approval(
    request_id: UUID,
    company_id: UUID,
    current_user=Depends(require_current_user),
):
    require_company_member(current_user, company_id)
    req = approval_service.get(request_id, company_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return req


@router.post("/{request_id}/approve", response_model=ApprovalRequest)
async def approve_request(
    request_id: UUID,
    company_id: UUID,
    current_user=Depends(require_current_user),
):
    require_company_member(current_user, company_id, action="approve AI operations for")
    req = approval_service.approve(request_id, company_id, current_user.user.id)
    if not req:
        raise HTTPException(status_code=400, detail="Cannot approve request")
    return req


@router.post("/{request_id}/reject", response_model=ApprovalRequest)
async def reject_request(
    request_id: UUID,
    company_id: UUID,
    current_user=Depends(require_current_user),
):
    require_company_member(current_user, company_id)
    req = approval_service.reject(request_id, company_id, current_user.user.id)
    if not req:
        raise HTTPException(status_code=400, detail="Cannot reject request")
    return req


@router.post("/{request_id}/cancel", response_model=ApprovalRequest)
async def cancel_request(
    request_id: UUID,
    company_id: UUID,
    current_user=Depends(require_current_user),
):
    require_company_member(current_user, company_id)
    req = approval_service.cancel(request_id, company_id, current_user.user.id)
    if not req:
        raise HTTPException(status_code=400, detail="Cannot cancel request")
    return req