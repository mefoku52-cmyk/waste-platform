"""Tool result."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Normalized result returned from a tool boundary."""

    request_id: str
    tool_name: str
    success: bool
    data: Any = None
    error_code: str | None = None
    error_message: str | None = None
