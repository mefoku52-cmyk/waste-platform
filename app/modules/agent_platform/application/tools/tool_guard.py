"""Tool guard contract."""

from abc import ABC, abstractmethod

from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class ToolGuard(ABC):
    @abstractmethod
    async def validate(self, request: ToolRequest) -> ToolResult | None:
        """Return a denial/error result, or None when validation passes."""
        raise NotImplementedError
