"""Agent execution pipeline stages.

The stage is descriptive only. It does not execute anything.
"""

from enum import StrEnum


class PipelineStage(StrEnum):
    MODEL_PROPOSAL = "model_proposal"
    POLICY_EVALUATION = "policy_evaluation"
    PERMISSION_EVALUATION = "permission_evaluation"
    APPROVAL_EVALUATION = "approval_evaluation"
    TOOL_DISPATCH = "tool_dispatch"
    CMEP_SERVICE_EXECUTION = "cmep_service_execution"
    AUDIT = "audit"
    EVENT_PUBLICATION = "event_publication"
    COMPLETED = "completed"
    DENIED = "denied"
    BLOCKED = "blocked"
    AWAITING_APPROVAL = "awaiting_approval"
