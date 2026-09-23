"""Tool definition."""

from dataclasses import dataclass, field

from .tool_risk import ToolRisk


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Description of a callable CMEP capability.

    The tool definition describes the boundary. It does not execute anything.
    """

    name: str
    description: str
    domain: str
    action: str
    risk: ToolRisk
    enabled: bool = True
    requires_approval: bool = False
    allowed_actor_types: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("tool name is required")
        if not self.domain.strip():
            raise ValueError("tool domain is required")
        if not self.action.strip():
            raise ValueError("tool action is required")
