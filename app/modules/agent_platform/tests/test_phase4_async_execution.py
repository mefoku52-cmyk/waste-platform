"""Phase 4 tests for the asynchronous tool execution boundary."""

import pytest

from app.modules.agent_platform.application.agent.agent_runtime import AgentRuntime
from app.modules.agent_platform.application.pipeline.agent_pipeline import AgentPipeline
from app.modules.agent_platform.infrastructure.testing.phase3_adapters import (
    AllowAllPermissionForTest,
    AllowAllPolicyForTest,
    ApprovalForSelectedTools,
    DeterministicModel,
    DeterministicToolExecutor,
    MemoryAudit,
    MemoryEvents,
)


def build_runtime(tools):
    return AgentRuntime(
        pipeline=AgentPipeline(
            model=DeterministicModel(),
            policy=AllowAllPolicyForTest(),
            permission=AllowAllPermissionForTest(),
            approval=ApprovalForSelectedTools(set()),
            tools=tools,
            audit=MemoryAudit(),
            events=MemoryEvents(),
        )
    )


@pytest.mark.asyncio
async def test_async_tool_execution_completes():
    tools = DeterministicToolExecutor()
    runtime = build_runtime(tools)

    result = await runtime.execute_tool(
        request_id="phase4-async-1",
        actor_id="user-1",
        actor_type="user",
        agent_id="cmep-user-ai",
        tool_name="cmep.company.search",
        arguments={"q": "recycling"},
        reason="phase4 async execution test",
    )

    assert result.decision.status.value == "executed"
    assert result.output.success is True
    assert len(tools.executed) == 1
    assert tools.executed[0].tool_name == "cmep.company.search"


@pytest.mark.asyncio
async def test_approval_stops_before_async_tool_execution():
    tools = DeterministicToolExecutor()

    runtime = AgentRuntime(
        pipeline=AgentPipeline(
            model=DeterministicModel(),
            policy=AllowAllPolicyForTest(),
            permission=AllowAllPermissionForTest(),
            approval=ApprovalForSelectedTools({"cmep.inquiry.send"}),
            tools=tools,
            audit=MemoryAudit(),
            events=MemoryEvents(),
        )
    )

    result = await runtime.execute_tool(
        request_id="phase4-approval-1",
        actor_id="user-1",
        actor_type="user",
        agent_id="cmep-user-ai",
        tool_name="cmep.inquiry.send",
        arguments={"listing_id": "listing-1"},
        reason="phase4 approval test",
    )

    assert result.decision.status.value == "awaiting_approval"
    assert result.output is None
    assert tools.executed == []


@pytest.mark.asyncio
async def test_async_pipeline_preserves_request_identity():
    tools = DeterministicToolExecutor()
    runtime = build_runtime(tools)

    result = await runtime.execute_tool(
        request_id="phase4-identity-1",
        actor_id="user-42",
        actor_type="user",
        agent_id="cmep-user-ai",
        tool_name="cmep.notifications.read",
        arguments={},
    )

    assert result.output.request_id == "phase4-identity-1"
    assert result.output.tool_name == "cmep.notifications.read"
