"""Tool registry contract."""

from abc import ABC, abstractmethod

from ...domain.tools.tool_definition import ToolDefinition


class ToolRegistry(ABC):
    @abstractmethod
    def register(self, definition: ToolDefinition) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, name: str) -> ToolDefinition | None:
        raise NotImplementedError

    @abstractmethod
    def list_available(self) -> tuple[ToolDefinition, ...]:
        raise NotImplementedError
