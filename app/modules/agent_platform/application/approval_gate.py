"""DB-backed approval gate for AgentOrchestrator with hash verification."""

from __future__ import annotations

import hashlib
import json
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


def _hash_args(arguments: dict[str, Any]) -> str:
    raw = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


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
            model = await self._repo.get(existing_approval_id, company_id)
            if not model:
                return ApprovalDecision(blocked=True, status="NOT_FOUND", message="Approval not found")
            if model.status != ApprovalStatus.APPROVED.value:
                return ApprovalDecision(blocked=True, status=model.status, approval_id=existing_approval_id)

            # Hash verification – reject if payload changed
            current_hash = _hash_args(arguments)
            if model.arguments_hash != current_hash:
                return ApprovalDecision(
                    blocked=True,
                    status="HASH_MISMATCH",
                    approval_id=existing_approval_id,
                    message="Payload changed after approval",
                )

            ok = await self._repo.transition_status(
                existing_approval_id,
                company_id,
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.EXECUTING.value,
            )
            if not ok:
                return ApprovalDecision(blocked=True, status="RACE", message="Concurrent execution")
            return ApprovalDecision(blocked=False, status="EXECUTING", approval_id=existing_approval_id)

        # Create new request and persist
        req = approval_service.create(
            actor_id=actor_id,
            company_id=company_id,
            tool_name=tool_name,
            arguments=arguments,
            description=f"AI tool {tool_name} requires approval",
            risk_level=risk,
        )
        # Persist via repository (in full production path)
        # await self._repo.add(...)
        return ApprovalDecision(
            blocked=True,
            status="PENDING_APPROVAL",
            approval_id=req.id,
            message="Operation requires approval",
        )