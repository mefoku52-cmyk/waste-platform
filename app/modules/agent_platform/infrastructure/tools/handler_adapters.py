"""Adapters from Agent Platform tools to existing CMEP services."""

from collections.abc import Awaitable, Callable
from typing import Any

from ...application.tools.tool_handler import ToolHandler
from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class CallableToolHandler(ToolHandler):
    """Adapts an injected async application-service callable."""

    def __init__(
        self,
        tool_name: str,
        callback: Callable[[ToolRequest], Awaitable[Any]],
    ) -> None:
        self.tool_name = tool_name
        self.callback = callback

    async def handle(self, request: ToolRequest) -> ToolResult:
        if request.tool_name != self.tool_name:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="handler_tool_mismatch",
                error_message="Handler is registered for another tool",
            )

        data = await self.callback(request)

        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data=data,
        )


class UnwiredToolHandler(ToolHandler):
    """Safe placeholder until an existing CMEP service is injected."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name

    async def handle(self, request: ToolRequest) -> ToolResult:
        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=False,
            error_code="tool_not_wired",
            error_message="Tool handler is not connected to a CMEP service",
        )


class CompanySearchToolHandler:
    """Phase 5 adapter for the existing CMEP company search service.

    Authorization is supplied by the authenticated application boundary.
    Tool arguments are never allowed to override the authorized company
    scope.
    """

    _ALLOWED_ARGUMENTS = frozenset(
        {
            "status",
            "company_type",
            "seller_capability",
            "buyer_capability",
            "logistics_capability",
            "q",
            "page",
            "page_size",
        }
    )

    def __init__(
        self,
        *,
        service,
        is_platform_admin: bool,
        company_ids: tuple[str, ...],
    ):
        self._service = service
        self._is_platform_admin = bool(is_platform_admin)
        self._company_ids = tuple(company_ids)

    async def __call__(self, request):
        arguments = dict(request.arguments or {})

        unknown = set(arguments) - self._ALLOWED_ARGUMENTS
        if unknown:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message=(
                    "Unsupported company search arguments: " + ", ".join(sorted(unknown))
                ),
            )

        # A non-admin with no authorized company membership has no
        # company-search scope. Never let the model manufacture one.
        if not self._is_platform_admin and not self._company_ids:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="company_access_denied",
                error_message="No authorized company scope.",
            )

        page = arguments.get("page", 1)
        page_size = arguments.get("page_size", 25)

        try:
            page = int(page)
            page_size = int(page_size)
        except (TypeError, ValueError):
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="page and page_size must be integers.",
            )

        if page < 1:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="page must be >= 1.",
            )

        if page_size < 1 or page_size > 100:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="page_size must be between 1 and 100.",
            )

        items, total = await self._service.execute(
            status=arguments.get("status"),
            company_type=arguments.get("company_type"),
            seller_capability=arguments.get("seller_capability"),
            buyer_capability=arguments.get("buyer_capability"),
            logistics_capability=arguments.get("logistics_capability"),
            q=arguments.get("q"),
            page=page,
            page_size=page_size,
            # Critical security boundary:
            # never accept company_ids from ToolRequest.arguments.
            company_ids=None if self._is_platform_admin else list(self._company_ids),
        )

        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        )
