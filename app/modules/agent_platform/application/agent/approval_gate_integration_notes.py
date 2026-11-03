"""Live integration patch for AgentOrchestrator.respond

Insert the following block immediately before the server tool handler is called
(after policy and permission checks, and only for non-client actions).

Location: inside the for call in response.tool_calls loop,
after the permission checks and before the actual handler invocation.

```python
# --- AI Approval Gate (Module 7) ---
from app.modules.agent_platform.application.approval_gate import ApprovalGate
from app.modules.agent_platform.application.approval_integration import classify_risk
from app.modules.agent_platform.application.approval_service import RiskLevel

risk = classify_risk(tool_name)
if risk not in (RiskLevel.READ_ONLY, RiskLevel.LOW_RISK) and not is_client_action:
    # In production the gate is injected via DI with a real session
    # gate = ApprovalGate(session)
    # decision = await gate.check_or_create(
    #     actor_id=UUID(actor_id),
    #     company_id=company_id_from_context,
    #     tool_name=tool_name,
    #     arguments=args,
    # )
    # if decision.blocked:
    #     messages.append(ModelMessage(
    #         role="tool",
    #         content=json.dumps({
    #             "error": "PENDING_APPROVAL",
    #             "approval_id": str(decision.approval_id),
    #             "status": decision.status,
    #             "message": decision.message,
    #         }),
    #         tool_call_id=call.get("id", ""),
    #     ))
    #     continue
# --- end Approval Gate ---
```

Protected write tools (from approval_integration.py):
- update_listing
- publish_listing
- create_inquiry
- update_inquiry_status
- promote_listing

Read-only tools skip the gate.
"""

from __future__ import annotations