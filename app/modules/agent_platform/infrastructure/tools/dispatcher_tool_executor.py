"""ToolExecutor backed by the controlled dispatcher."""

from ...application.tools.tool_dispatcher import ToolDispatcher
from ...application.tools.tool_executor import ToolExecutor
from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


class DispatcherToolExecutor(ToolExecutor):
    """Connects AgentPipeline to the controlled tool dispatcher."""

    def __init__(self, dispatcher: ToolDispatcher) -> None:
        self.dispatcher = dispatcher

    async def execute(self, request: ToolRequest) -> ToolResult:
        return await self.dispatcher.dispatch(request)
