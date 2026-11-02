"""Orchestrator hook – requires real session and company_id.

Call this from AgentOrchestrator.respond with values passed from the chat router.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.approval_gate import ApprovalDecision, ApprovalGate


async def check_approval(
    session: AsyncSession,
    actor_id: UUID,
    company_id: UUID,
    tool_name: str,
    arguments: dict[str, Any],
    existing_approval_id: UUID | None = None,
) -> ApprovalDecision:
    if session is None or company_id is None:
        raise RuntimeError("Approval requires real DB session and company context")
    gate = ApprovalGate(session)
    return await gate.check_or_create(
        actor_id=actor_id,
        company_id=company_id,
        tool_name=tool_name,
        arguments=arguments,
        existing_approval_id=existing_approval_id,
    )