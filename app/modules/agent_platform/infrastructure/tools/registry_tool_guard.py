"""Default registry-backed tool guard."""

from ...application.tools.tool_guard import ToolGuard
from ...application.tools.tool_registry import ToolRegistry
from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class RegistryToolGuard(ToolGuard):
    """Performs structural tool checks after policy/permission decisions."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    async def validate(self, request: ToolRequest) -> ToolResult | None:
        definition = self.registry.get(request.tool_name)

        if definition is None:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="unknown_tool",
                error_message="Tool is not registered",
            )

        if getattr(definition, "enabled", True) is False:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="tool_disabled",
                error_message="Tool is disabled",
            )

        allowed_actor_types = getattr(
            definition,
            "allowed_actor_types",
            getattr(definition, "actor_types", None),
        )

        if allowed_actor_types is not None:
            if request.actor_type not in set(allowed_actor_types):
                return ToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    success=False,
                    error_code="actor_not_allowed",
                    error_message="Actor type is not allowed for this tool",
                )

        return None
