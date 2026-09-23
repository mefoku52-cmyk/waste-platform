"""Tool handler registry contract."""

from abc import ABC, abstractmethod

from .tool_handler import ToolHandler


class ToolHandlerRegistry(ABC):
    """Maps tool names to application-level handlers."""

    @abstractmethod
    def register(self, tool_name: str, handler: ToolHandler) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, tool_name: str) -> ToolHandler | None:
        raise NotImplementedError

    @abstractmethod
    def list_registered(self) -> tuple[str, ...]:
        raise NotImplementedError
