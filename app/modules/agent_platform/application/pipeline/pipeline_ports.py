"""Ports consumed by the agent execution pipeline.

These are application-level contracts only.
Concrete infrastructure adapters are intentionally deferred.
"""

from __future__ import annotations

from typing import Any, Protocol

from ...domain.approval.approval_request import ApprovalRequest
from ...domain.permission.permission_request import PermissionRequest
from ...domain.policy.policy_context import PolicyContext
from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult
from ..decisions.pipeline_decision import PipelineDecision
from ..pipeline.pipeline_request import PipelineRequest


class ModelProposalPort(Protocol):
    """Produces a proposed tool request.

    The model proposes.
    It never authorizes.
    """

    def propose(self, request: PipelineRequest) -> ToolRequest: ...


class PolicyPort(Protocol):
    """Evaluates whether the proposed action is allowed by policy."""

    def evaluate(self, context: PolicyContext) -> PipelineDecision: ...


class PermissionPort(Protocol):
    """Evaluates actor permission independently from model output."""

    def evaluate(self, request: PermissionRequest) -> PipelineDecision: ...


class ApprovalPort(Protocol):
    """Creates or checks human approval for sensitive actions."""

    def requires_approval(self, tool_name: str) -> bool: ...

    def create_request(self, request: ApprovalRequest) -> str: ...


class ToolPort(Protocol):
    """Dispatches an already-authorized tool request asynchronously."""

    async def execute(self, request: ToolRequest) -> ToolResult: ...


class AuditPort(Protocol):
    """Records the pipeline outcome."""

    def record(self, request: PipelineRequest, result: PipelineDecision) -> None: ...


class EventPort(Protocol):
    """Publishes an application event."""

    def publish(self, event_name: str, payload: dict[str, Any]) -> None: ...
