"""DB-backed approval gate for AgentOrchestrator.

Production path. Uses repository for all state changes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.approval_integration import classify_risk
from app.modules.agent_platform.application.approval_service import (
    ApprovalStatus,
    RiskLevel,
)
from app.modules.agent_platform.infrastructure.models.ai_approval import AiApprovalRequestModel
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
                return ApprovalDecision(blocked=True, status="NOT_FOUND")
            if model.status != ApprovalStatus.APPROVED.value:
                return ApprovalDecision(blocked=True, status=model.status, approval_id=existing_approval_id)
            if model.arguments_hash != _hash_args(arguments):
                return ApprovalDecision(blocked=True, status="HASH_MISMATCH", approval_id=existing_approval_id)
            if model.expires_at < datetime.now(UTC):
                return ApprovalDecision(blocked=True, status="EXPIRED", approval_id=existing_approval_id)

            ok = await self._repo.transition_status(
                existing_approval_id,
                company_id,
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.EXECUTING.value,
            )
            if not ok:
                return ApprovalDecision(blocked=True, status="RACE")
            return ApprovalDecision(blocked=False, status="EXECUTING", approval_id=existing_approval_id)

        # Create and persist
        req_id = uuid4()
        model = AiApprovalRequestModel(
            id=req_id,
            actor_id=actor_id,
            company_id=company_id,
            tool_name=tool_name,
            arguments=arguments,
            arguments_hash=_hash_args(arguments),
            description=f"AI tool {tool_name} requires approval",
            risk_level=risk.value,
            status=ApprovalStatus.PENDING.value,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
            created_at=datetime.now(UTC),
        )
        await self._repo.add(model)
        return ApprovalDecision(
            blocked=True,
            status="PENDING_APPROVAL",
            approval_id=req_id,
            message="Operation requires approval",
        )