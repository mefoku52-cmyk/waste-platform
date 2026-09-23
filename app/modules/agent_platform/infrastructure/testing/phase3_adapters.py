"""Deterministic Phase 3 test adapters.

These implementations exist solely to prove pipeline ordering.
They intentionally contain no external I/O.
"""

from __future__ import annotations

from ...application.decisions.pipeline_decision import PipelineDecision
from ...application.pipeline.pipeline_request import PipelineRequest
from ...domain.approval.approval_request import ApprovalRequest
from ...domain.permission.permission_request import PermissionRequest
from ...domain.pipeline.pipeline_stage import PipelineStage
from ...domain.pipeline.pipeline_status import PipelineStatus
from ...domain.policy.policy_context import PolicyContext
from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class DeterministicModel:
    """Model stub that deterministically proposes the requested tool."""

    def propose(self, request: PipelineRequest) -> ToolRequest:
        return ToolRequest(
            request_id=request.context.request_id,
            tool_name=request.tool_name,
            actor_id=request.context.actor_id,
            actor_type=request.context.actor_type,
            arguments=request.arguments,
            reason=request.reason or "phase3_test_request",
        )


class AllowAllPolicyForTest:
    """Deterministic policy adapter for Phase 3 tests."""

    def evaluate(self, context: PolicyContext) -> PipelineDecision:
        return PipelineDecision(
            status=PipelineStatus.ALLOWED,
            stage=PipelineStage.POLICY_EVALUATION,
            reason="test_policy_allows",
            metadata={},
        )


class AllowAllPermissionForTest:
    """Deterministic permission adapter for Phase 3 tests."""

    def evaluate(self, request: PermissionRequest) -> PipelineDecision:
        return PipelineDecision(
            status=PipelineStatus.ALLOWED,
            stage=PipelineStage.PERMISSION_EVALUATION,
            reason="test_permission_allows",
            metadata={},
        )


class DenyPolicyForTest:
    """Deterministic denying policy adapter for Phase 3 tests."""

    def evaluate(self, context: PolicyContext) -> PipelineDecision:
        return PipelineDecision(
            status=PipelineStatus.BLOCKED,
            stage=PipelineStage.POLICY_EVALUATION,
            reason="test_policy_denies",
            metadata={},
        )


class ApprovalForSelectedTools:
    """Deterministic approval adapter for Phase 3 tests."""

    def __init__(self, tools_requiring_approval: set[str]):
        self.tools_requiring_approval = tools_requiring_approval
        self.created: list[ApprovalRequest] = []

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.tools_requiring_approval

    def create_request(self, request: ApprovalRequest) -> str:
        self.created.append(request)
        return request.approval_id


class DeterministicToolExecutor:
    """Deterministic tool executor with no external I/O."""

    def __init__(self):
        self.executed: list[ToolRequest] = []

    async def execute(self, request: ToolRequest) -> ToolResult:
        self.executed.append(request)

        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={"tool": request.tool_name},
        )


class MemoryAudit:
    """In-memory audit sink for tests."""

    def __init__(self):
        self.records = []

    def record(
        self,
        request: PipelineRequest,
        result: PipelineDecision,
    ) -> None:
        self.records.append((request, result))


class MemoryEvents:
    """In-memory event sink for tests."""

    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def publish(self, event_name: str, payload: dict) -> None:
        self.events.append((event_name, payload))
