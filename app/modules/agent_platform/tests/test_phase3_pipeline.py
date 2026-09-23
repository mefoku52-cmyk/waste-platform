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


def build_runtime(approval_tools=None):
    approval = ApprovalForSelectedTools(approval_tools or set())
    tools = DeterministicToolExecutor()
    audit = MemoryAudit()
    events = MemoryEvents()

    pipeline = AgentPipeline(
        model=DeterministicModel(),
        policy=AllowAllPolicyForTest(),
        permission=AllowAllPermissionForTest(),
        approval=approval,
        tools=tools,
        audit=audit,
        events=events,
    )

    return (
        AgentRuntime(pipeline=pipeline),
        approval,
        tools,
        audit,
        events,
    )


@pytest.mark.asyncio
async def test_low_risk_tool_reaches_executor():
    runtime, approval, tools, audit, events = build_runtime()

    result = await runtime.execute_tool(
        request_id="req-1",
        actor_id="user-1",
        actor_type="user",
        agent_id="cmep-user-ai",
        tool_name="cmep.company.search",
        arguments={"query": "plastics"},
    )

    assert result.decision.status.value == "executed"
    assert len(tools.executed) == 1
    assert len(approval.created) == 0
    assert len(audit.records) == 1
    assert len(events.events) == 2


@pytest.mark.asyncio
async def test_sensitive_tool_stops_for_human_approval():
    runtime, approval, tools, audit, events = build_runtime({"cmep.inquiry.send"})

    result = await runtime.execute_tool(
        request_id="req-2",
        actor_id="user-1",
        actor_type="user",
        agent_id="cmep-user-ai",
        tool_name="cmep.inquiry.send",
        arguments={"listing_id": "listing-1"},
        reason="User requested inquiry transmission.",
    )

    assert result.decision.status.value == "awaiting_approval"
    assert len(tools.executed) == 0
    assert len(approval.created) == 1
    assert approval.created[0].action == "cmep.inquiry.send"
    assert len(audit.records) == 1
    assert len(events.events) == 2


@pytest.mark.asyncio
async def test_pipeline_records_denial_before_execution():
    class DenyPolicy:
        def evaluate(self, context):
            from app.modules.agent_platform.application.decisions.pipeline_decision import (
                PipelineDecision,
            )
            from app.modules.agent_platform.domain.pipeline.pipeline_stage import (
                PipelineStage,
            )
            from app.modules.agent_platform.domain.pipeline.pipeline_status import (
                PipelineStatus,
            )

            return PipelineDecision(
                status=PipelineStatus.DENIED,
                stage=PipelineStage.POLICY_EVALUATION,
                reason="test_policy_denied",
                metadata={},
            )

    approval = ApprovalForSelectedTools(set())
    tools = DeterministicToolExecutor()
    audit = MemoryAudit()
    events = MemoryEvents()

    pipeline = AgentPipeline(
        model=DeterministicModel(),
        policy=DenyPolicy(),
        permission=AllowAllPermissionForTest(),
        approval=approval,
        tools=tools,
        audit=audit,
        events=events,
    )

    runtime = AgentRuntime(pipeline=pipeline)

    result = await runtime.execute_tool(
        request_id="req-3",
        actor_id="user-1",
        actor_type="user",
        agent_id="cmep-user-ai",
        tool_name="cmep.company.search",
        arguments={},
    )

    assert result.decision.status.value == "denied"
    assert len(tools.executed) == 0
    assert len(audit.records) == 1
