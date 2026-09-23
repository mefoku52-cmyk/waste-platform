"""In-memory tool handler registry."""

from ...application.tools.tool_handler import ToolHandler
from ...application.tools.tool_handler_registry import ToolHandlerRegistry


class InMemoryToolHandlerRegistry(ToolHandlerRegistry):
    """Deterministic registry for injected tool handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, tool_name: str, handler: ToolHandler) -> None:
        name = tool_name.strip()
        if not name:
            raise ValueError("tool_name must not be empty")
        if name in self._handlers:
            raise ValueError(f"tool handler already registered: {name}")
        self._handlers[name] = handler

    def get(self, tool_name: str) -> ToolHandler | None:
        return self._handlers.get(tool_name)

    def list_registered(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))
