"""Controlled tool dispatcher."""

from abc import ABC, abstractmethod

from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class ToolDispatcher(ABC):
    """Dispatches only registered and policy-approved tools."""

    @abstractmethod
    async def dispatch(self, request: ToolRequest) -> ToolResult:
        raise NotImplementedError
