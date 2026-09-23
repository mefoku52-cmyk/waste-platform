"""Immutable decision result used by the agent pipeline."""

from dataclasses import dataclass
from typing import Any

from ...domain.pipeline.pipeline_stage import PipelineStage
from ...domain.pipeline.pipeline_status import PipelineStatus


@dataclass(frozen=True, slots=True)
class PipelineDecision:
    status: PipelineStatus
    stage: PipelineStage
    reason: str
    metadata: dict[str, Any]

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            PipelineStatus.DENIED,
            PipelineStatus.BLOCKED,
            PipelineStatus.EXECUTED,
            PipelineStatus.FAILED,
        }
