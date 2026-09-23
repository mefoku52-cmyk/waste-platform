"""Request entering the agent execution pipeline."""

from dataclasses import dataclass, field
from typing import Any

from ..runtime.runtime_context import AgentRuntimeContext


@dataclass(frozen=True, slots=True)
class PipelineRequest:
    context: AgentRuntimeContext
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
