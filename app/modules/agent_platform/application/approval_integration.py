"""Integration notes for wiring AI Approval into AgentOrchestrator.

In AgentOrchestrator.respond, before executing a server tool:

1. Classify risk deterministically (not by LLM).
2. If risk >= MEDIUM and tool is write:
   - Create ApprovalRequest via ApprovalService
   - Return tool message with {"error": "requires_approval", "approval_id": "..."}
   - Do not execute the handler.
3. On later execution request:
   - Load ApprovalRequest from DB
   - Verify status == APPROVED, hash matches, not expired, tenant matches
   - Atomically transition APPROVED → EXECUTING
   - Execute the original tool handler with stored arguments
   - Transition to EXECUTED or FAILED
   - Write audit

Read-only tools skip this path.
"""

from __future__ import annotations

from app.modules.agent_platform.application.approval_service import RiskLevel

WRITE_TOOLS_REQUIRING_APPROVAL = {
    "update_listing",
    "publish_listing",
    "create_inquiry",
    "update_inquiry_status",
    "promote_listing",
}

def classify_risk(tool_name: str) -> RiskLevel:
    if tool_name in WRITE_TOOLS_REQUIRING_APPROVAL:
        return RiskLevel.HIGH_RISK
    if tool_name.startswith("get_") or tool_name.startswith("list_"):
        return RiskLevel.READ_ONLY
    return RiskLevel.LOW_RISK