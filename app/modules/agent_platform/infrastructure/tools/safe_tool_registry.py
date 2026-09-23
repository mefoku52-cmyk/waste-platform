"""Safety-wrapped tool registry."""

from ...application.tools.tool_registry import ToolRegistry
from ...domain.tools.tool_definition import ToolDefinition
from .forbidden_tool_names import is_forbidden_tool_name


class SafeToolRegistry(ToolRegistry):
    """Tool registry that rejects forbidden capability names."""

    def __init__(self, inner: ToolRegistry) -> None:
        self._inner = inner

    def register(self, definition: ToolDefinition) -> None:
        if is_forbidden_tool_name(definition.name):
            raise ValueError(f"Forbidden tool capability: {definition.name}")

        self._inner.register(definition)

    def get(self, name: str) -> ToolDefinition | None:
        if is_forbidden_tool_name(name):
            return None

        return self._inner.get(name)

    def list_available(self) -> tuple[ToolDefinition, ...]:
        return tuple(
            definition
            for definition in self._inner.list_available()
            if not is_forbidden_tool_name(definition.name)
        )
