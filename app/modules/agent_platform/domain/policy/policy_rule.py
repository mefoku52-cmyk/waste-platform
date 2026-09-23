"""Policy rule."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """A policy rule evaluated by the application policy engine."""

    rule_id: str
    name: str
    action: str
    enabled: bool = True
    parameters: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.action.strip():
            raise ValueError("action is required")
