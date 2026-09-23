"""Controlled Agent Platform tool dispatcher."""

from ...application.tools.tool_dispatcher import ToolDispatcher
from ...application.tools.tool_guard import ToolGuard
from ...application.tools.tool_handler_registry import ToolHandlerRegistry
from ...application.tools.tool_registry import ToolRegistry
from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class CMEPToolDispatcher(ToolDispatcher):
    """Routes approved tool requests to registered application handlers."""

    def __init__(
        self,
        *,
        registry: ToolRegistry,
        guard: ToolGuard,
        handlers: ToolHandlerRegistry,
    ) -> None:
        self.registry = registry
        self.guard = guard
        self.handlers = handlers

    async def dispatch(self, request: ToolRequest) -> ToolResult:
        if self.registry.get(request.tool_name) is None:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="unknown_tool",
                error_message="Tool is not registered",
            )

        guard_result = await self.guard.validate(request)
        if guard_result is not None:
            return guard_result

        handler = self.handlers.get(request.tool_name)
        if handler is None:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="handler_not_registered",
                error_message="Tool has no execution handler",
            )

        try:
            result = await handler.handle(request)
        except Exception:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="tool_execution_error",
                error_message="Tool execution failed",
            )

        if result.request_id != request.request_id:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="handler_identity_mismatch",
                error_message="Tool handler returned an invalid request identity",
            )

        if result.tool_name != request.tool_name:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="handler_tool_mismatch",
                error_message="Tool handler returned an invalid tool identity",
            )

        return result
