"""Tool handler contract."""

from abc import ABC, abstractmethod

from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class ToolHandler(ABC):
    """Executes one registered Agent Platform tool."""

    @abstractmethod
    async def handle(self, request: ToolRequest) -> ToolResult:
        raise NotImplementedError
