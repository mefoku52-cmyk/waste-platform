"""Provider-neutral AI model request."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelMessage:
    """Single normalized model message."""

    role: str
    content: str

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("message role is required")


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """Provider-neutral model invocation request.

    The Agent Platform owns policy and tool authorization.
    A model provider must never be treated as an authority.
    """

    request_id: str
    model: str
    messages: tuple[ModelMessage, ...]
    system_instruction: str | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.model.strip():
            raise ValueError("model is required")
        if not self.messages:
            raise ValueError("at least one message is required")

        if self.temperature is not None:
            if not 0.0 <= self.temperature <= 2.0:
                raise ValueError("temperature must be between 0 and 2")

        if self.max_output_tokens is not None:
            if self.max_output_tokens <= 0:
                raise ValueError("max_output_tokens must be positive")
