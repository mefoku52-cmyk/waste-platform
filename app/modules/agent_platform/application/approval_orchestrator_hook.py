"""Thin wrapper that AgentOrchestrator.respond should call before write tools.

Insert this call in agent_orchestrator.py inside the tool loop,
after policy and permission checks, before handler invocation:

    from app.modules.agent_platform.application.approval_orchestrator_hook import check_approval

    decision = await check_approval(
        session=db_session,          # must be injected
        actor_id=UUID(actor_id),
        company_id=company_id,       # from context
        tool_name=tool_name,
        arguments=args,
    )
    if decision.blocked:
        messages.append(ModelMessage(
            role="tool",
            content=json.dumps({
                "error": "PENDING_APPROVAL",
                "approval_id": str(decision.approval_id),
                "status": decision.status,
            }),
            tool_call_id=call.get("id", ""),
        ))
        continue
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
    gate = ApprovalGate(session)
    return await gate.check_or_create(
        actor_id=actor_id,
        company_id=company_id,
        tool_name=tool_name,
        arguments=arguments,
        existing_approval_id=existing_approval_id,
    )