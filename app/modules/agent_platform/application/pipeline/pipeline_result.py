"""Result leaving the agent execution pipeline."""

from dataclasses import dataclass, field
from typing import Any

from ..decisions.pipeline_decision import PipelineDecision


@dataclass(frozen=True, slots=True)
class PipelineResult:
    decision: PipelineDecision
    output: Any = None
    events: tuple[str, ...] = field(default_factory=tuple)
    audit_recorded: bool = False
