"""Tool executor contract."""

from abc import ABC, abstractmethod

from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class ToolExecutor(ABC):
    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResult:
        raise NotImplementedError
