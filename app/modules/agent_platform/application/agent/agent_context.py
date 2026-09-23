"""Agent context contract."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Structured context supplied to the model.

    Raw database access is deliberately absent from this object.
    """

    user_id: str | None
    company_id: str | None
    session_id: str
    locale: str | None = None
    conversation: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    business_context: dict[str, Any] = field(default_factory=dict)
    available_tools: tuple[str, ...] = field(default_factory=tuple)
    security_context: dict[str, Any] = field(default_factory=dict)
