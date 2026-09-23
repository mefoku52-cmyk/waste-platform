"""Main Agent Platform execution pipeline.

The orchestrator coordinates boundaries.
It does not own:
- authentication
- business authorization
- database access
- SQL
- shell access
- filesystem access
- model credentials
- business service implementation

The model may propose.
Only policy, permission, approval and existing CMEP services determine
what can actually happen.
"""

from dataclasses import dataclass
from datetime import UTC

from ...domain.pipeline.pipeline_stage import PipelineStage
from ...domain.pipeline.pipeline_status import PipelineStatus
from ..decisions.pipeline_decision import PipelineDecision
from ..pipeline.pipeline_request import PipelineRequest
from ..pipeline.pipeline_result import PipelineResult
from .pipeline_ports import (
    ApprovalPort,
    AuditPort,
    EventPort,
    ModelProposalPort,
    PermissionPort,
    PolicyPort,
    ToolPort,
)


@dataclass(frozen=True, slots=True)
class AgentPipeline:
    model: ModelProposalPort
    policy: PolicyPort
    permission: PermissionPort
    approval: ApprovalPort
    tools: ToolPort
    audit: AuditPort
    events: EventPort

    async def run(self, request: PipelineRequest) -> PipelineResult:
        self.events.publish(
            "agent.pipeline.started",
            {
                "request_id": request.context.request_id,
                "actor_id": request.context.actor_id,
                "tool_name": request.tool_name,
            },
        )

        proposed_tool = self.model.propose(request)

        if proposed_tool.tool_name != request.tool_name:
            decision = PipelineDecision(
                status=PipelineStatus.BLOCKED,
                stage=PipelineStage.MODEL_PROPOSAL,
                reason="model_proposal_tool_mismatch",
                metadata={
                    "requested_tool": request.tool_name,
                    "proposed_tool": proposed_tool.tool_name,
                },
            )
            return self._finish(request, decision)

        policy_decision = self.policy.evaluate(self._policy_context(request))

        if policy_decision.status != PipelineStatus.ALLOWED:
            return self._finish(request, policy_decision)

        permission_decision = self.permission.evaluate(self._permission_request(request))

        if permission_decision.status != PipelineStatus.ALLOWED:
            return self._finish(request, permission_decision)

        if self.approval.requires_approval(proposed_tool.tool_name):
            approval_id = self.approval.create_request(self._approval_request(request))

            decision = PipelineDecision(
                status=PipelineStatus.AWAITING_APPROVAL,
                stage=PipelineStage.APPROVAL_EVALUATION,
                reason="human_approval_required",
                metadata={"approval_id": approval_id},
            )

            return self._finish(request, decision)

        tool_result = await self.tools.execute(proposed_tool)

        decision = PipelineDecision(
            status=PipelineStatus.EXECUTED if tool_result.success else PipelineStatus.FAILED,
            stage=PipelineStage.TOOL_DISPATCH,
            reason=("tool_execution_completed" if tool_result.success else "tool_execution_failed"),
            metadata={
                "tool_name": proposed_tool.tool_name,
            },
        )

        return self._finish(
            request,
            decision,
            output=tool_result,
        )

    def _finish(
        self,
        request: PipelineRequest,
        decision: PipelineDecision,
        output=None,
    ) -> PipelineResult:
        self.audit.record(request, decision)

        self.events.publish(
            "agent.pipeline.completed",
            {
                "request_id": request.context.request_id,
                "actor_id": request.context.actor_id,
                "tool_name": request.tool_name,
                "status": decision.status.value,
                "stage": decision.stage.value,
                "reason": decision.reason,
            },
        )

        return PipelineResult(
            decision=decision,
            output=output,
            events=(
                "agent.pipeline.started",
                "agent.pipeline.completed",
            ),
            audit_recorded=True,
        )

    @staticmethod
    def _policy_context(request: PipelineRequest):
        from ...domain.policy.policy_context import PolicyContext

        return PolicyContext(
            actor_id=request.context.actor_id,
            actor_type=request.context.actor_type,
            agent_id=request.context.agent_id,
            action=request.tool_name,
            target=request.tool_name,
            tool_name=request.tool_name,
            risk_level=None,
            attributes={
                "request_id": request.context.request_id,
                "arguments": dict(request.arguments),
            },
        )

    @staticmethod
    def _permission_request(request: PipelineRequest):
        from ...domain.permission.permission_request import PermissionRequest
        from ...domain.permission.permission_scope import PermissionScope

        reason = request.reason or "agent pipeline execution request"

        return PermissionRequest(
            request_id=request.context.request_id,
            actor_id=request.context.actor_id,
            actor_type=request.context.actor_type,
            scope=PermissionScope(
                resource=request.tool_name,
                action=request.tool_name,
            ),
            reason=reason,
        )

    @staticmethod
    def _approval_request(request: PipelineRequest):
        from datetime import datetime, timedelta
        from uuid import uuid4

        from ...domain.approval.approval_request import ApprovalRequest

        created_at = datetime.now(UTC)

        return ApprovalRequest(
            approval_id=f"approval-{uuid4()}",
            requested_by=request.context.actor_id,
            requested_by_type=request.context.actor_type,
            action=request.tool_name,
            target=request.tool_name,
            reason=request.reason or "human approval required",
            risk_level="high",
            created_at=created_at,
            expires_at=created_at + timedelta(minutes=15),
        )
