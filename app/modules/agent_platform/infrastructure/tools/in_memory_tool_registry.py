"""Explicit in-memory tool registry.

This is intentionally small and safe.

No automatic discovery.
No filesystem scanning.
No importing arbitrary Python modules.
No shell execution.
No database introspection.

Concrete CMEP tools will be registered explicitly later.
"""

from ...application.tools.tool_registry import ToolRegistry
from ...domain.tools.tool_definition import ToolDefinition


class InMemoryToolRegistry(ToolRegistry):
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise ValueError(f"Tool already registered: {definition.name}")

        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_available(self) -> tuple[ToolDefinition, ...]:
        return tuple(definition for definition in self._tools.values() if definition.enabled)
