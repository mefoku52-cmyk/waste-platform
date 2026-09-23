"""High-level Agent Platform runtime facade."""

from dataclasses import dataclass

from ..pipeline.agent_pipeline import AgentPipeline
from ..pipeline.pipeline_request import PipelineRequest
from ..pipeline.pipeline_result import PipelineResult
from ..runtime.runtime_context import AgentRuntimeContext


@dataclass(frozen=True, slots=True)
class AgentRuntime:
    pipeline: AgentPipeline

    async def execute_tool(
        self,
        *,
        request_id: str,
        actor_id: str,
        actor_type: str,
        agent_id: str,
        tool_name: str,
        arguments: dict,
        reason: str = "",
        session_id: str | None = None,
    ) -> PipelineResult:
        context = AgentRuntimeContext(
            request_id=request_id,
            actor_id=actor_id,
            actor_type=actor_type,
            agent_id=agent_id,
            session_id=session_id,
        )

        return await self.pipeline.run(
            PipelineRequest(
                context=context,
                tool_name=tool_name,
                arguments=arguments,
                reason=reason,
            )
        )
