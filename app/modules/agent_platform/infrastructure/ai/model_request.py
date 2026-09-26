from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: str
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: tuple[dict[str, Any], ...] | None = None

    def __post_init__(self) -> None:
        if self.role not in ("system", "user", "assistant", "tool"):
            raise ValueError(f"Invalid role: {self.role}")
        if self.role == "tool" and not self.tool_call_id:
            raise ValueError("tool role requires tool_call_id")


@dataclass(frozen=True, slots=True)
class ModelRequest:
    request_id: str
    model: str
    messages: tuple[ModelMessage, ...]
    temperature: float = 0.2
    tools: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    tool_choice: str | None = None
