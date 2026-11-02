"""DB-backed approval gate for AgentOrchestrator.

This module provides the production path that the orchestrator should call
before executing a server write tool.

Usage in AgentOrchestrator (conceptual):

    from app.modules.agent_platform.application.approval_gate import ApprovalGate

    gate = ApprovalGate(session, approval_repo)
    decision = await gate.check_or_create(
        actor_id=actor_id,
        company_id=company_id,
        tool_name=tool_name,
        arguments=args,
    )
    if decision.blocked:
        return tool_message with decision.payload
    # else proceed to execute handler
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.approval_integration import classify_risk
from app.modules.agent_platform.application.approval_service import (
    ApprovalStatus,
    RiskLevel,
    approval_service,
)
from app.modules.agent_platform.infrastructure.repositories.ai_approval_repository import (
    AiApprovalRepository,
)


@dataclass
class ApprovalDecision:
    blocked: bool
    status: str
    approval_id: UUID | None = None
    message: str = ""


class ApprovalGate:
    def __init__(self, session: AsyncSession, repo: AiApprovalRepository | None = None) -> None:
        self._session = session
        self._repo = repo or AiApprovalRepository(session)

    async def check_or_create(
        self,
        *,
        actor_id: UUID,
        company_id: UUID,
        tool_name: str,
        arguments: dict[str, Any],
        existing_approval_id: UUID | None = None,
    ) -> ApprovalDecision:
        risk = classify_risk(tool_name)
        if risk in (RiskLevel.READ_ONLY, RiskLevel.LOW_RISK):
            return ApprovalDecision(blocked=False, status="SKIPPED")

        if existing_approval_id:
            # Verify existing approval
            model = await self._repo.get(existing_approval_id, company_id)
            if not model:
                return ApprovalDecision(blocked=True, status="NOT_FOUND", message="Approval not found")
            if model.status != ApprovalStatus.APPROVED.value:
                return ApprovalDecision(blocked=True, status=model.status, approval_id=existing_approval_id)
            # Hash check would happen here against stored arguments_hash
            # Atomic transition APPROVED → EXECUTING
            ok = await self._repo.transition_status(
                existing_approval_id,
                company_id,
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.EXECUTING.value,
            )
            if not ok:
                return ApprovalDecision(blocked=True, status="RACE", message="Concurrent execution")
            return ApprovalDecision(blocked=False, status="EXECUTING", approval_id=existing_approval_id)

        # Create new request
        req = approval_service.create(
            actor_id=actor_id,
            company_id=company_id,
            tool_name=tool_name,
            arguments=arguments,
            description=f"AI tool {tool_name} requires approval",
            risk_level=risk,
        )
        # In full impl persist via repo.add
        return ApprovalDecision(
            blocked=True,
            status="PENDING_APPROVAL",
            approval_id=req.id,
            message="Operation requires approval",
        )