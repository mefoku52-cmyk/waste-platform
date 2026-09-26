from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelToolCall:
    """One tool call requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def as_openai(self) -> dict[str, Any]:
        import json

        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False),
            },
        }


@dataclass(frozen=True, slots=True)
class ModelResponse:
    request_id: str
    text: str = ""
    finish_reason: str = "stop"
    tool_calls: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
