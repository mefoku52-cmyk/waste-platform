"""Provider-neutral AI model response."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelToolCall:
    """A model-proposed tool call.

    This is only a proposal. It is not execution authorization.
    """

    call_id: str
    tool_name: str
    arguments: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.call_id.strip():
            raise ValueError("call_id is required")
        if not self.tool_name.strip():
            raise ValueError("tool_name is required")


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Normalized provider response."""

    request_id: str
    text: str
    finish_reason: str | None = None
    tool_calls: tuple[ModelToolCall, ...] = field(default_factory=tuple)
    usage: dict[str, Any] = field(default_factory=dict)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
