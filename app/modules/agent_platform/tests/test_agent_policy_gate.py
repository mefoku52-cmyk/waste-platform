"""Policy gate tests – DENY must not call handler."""

from __future__ import annotations

import pytest

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.domain.policy.policy_context import PolicyContext
from app.modules.agent_platform.domain.policy.policy_decision import PolicyOutcome
from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse
from app.modules.agent_platform.infrastructure.policy.allowlist_policy_engine import (
    AllowlistPolicyEngine,
)


class _SpyHandler:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def handle(self, request) -> ToolResult:
        self.calls.append(request.tool_name)
        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={"ok": True},
        )


class _FakeGateway:
    def __init__(self, tool_name: str) -> None:
        self._tool_name = tool_name
        self.calls = 0

    def provider_name(self) -> str:
        return "fake"

    async def generate(self, request) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(
                request_id=request.request_id,
                text="",
                finish_reason="tool_calls",
                tool_calls=(
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": self._tool_name, "arguments": "{}"},
                    },
                ),
            )
        return ModelResponse(
            request_id=request.request_id,
            text="Hotovo.",
            finish_reason="stop",
            tool_calls=(),
        )


def _ctx(tool_name: str) -> PolicyContext:
    return PolicyContext(
        actor_id="u1",
        actor_type="user",
        agent_id=None,
        action="tool.call",
        target=None,
        tool_name=tool_name,
        risk_level=None,
        attributes={},
    )


@pytest.mark.asyncio
async def test_allowlist_policy_denies_unknown_tool() -> None:
    policy = AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_companies"}))
    decision = await policy.decide(_ctx("nope"))
    assert decision.outcome == PolicyOutcome.DENY
    assert decision.rule_id == "policy.unknown_tool"


@pytest.mark.asyncio
async def test_allowlist_policy_allows_known_tool() -> None:
    policy = AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_companies"}))
    decision = await policy.decide(_ctx("search_companies"))
    assert decision.outcome == PolicyOutcome.ALLOW


@pytest.mark.asyncio
async def test_allowlist_policy_denies_empty_tool() -> None:
    policy = AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_companies"}))
    decision = await policy.decide(_ctx(""))
    assert decision.outcome == PolicyOutcome.DENY
    assert decision.rule_id == "policy.missing_tool_name"


@pytest.mark.asyncio
async def test_orchestrator_denies_unknown_tool_without_calling_handler() -> None:
    gateway = _FakeGateway(tool_name="unknown_tool")
    spy = _SpyHandler()
    policy = AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_companies"}))

    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        policy=policy,
        model="test",
    )

    result = await orch.respond(
        system_prompt="sys",
        user_message="ahoj",
        actor_id="u1",
    )

    assert spy.calls == [], "Handler must not be called for a denied tool"
    assert result.text == "Hotovo."


@pytest.mark.asyncio
async def test_orchestrator_calls_handler_for_allowlisted_tool() -> None:
    gateway = _FakeGateway(tool_name="search_companies")
    spy = _SpyHandler()
    policy = AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_companies"}))

    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        policy=policy,
        model="test",
    )

    await orch.respond(
        system_prompt="sys",
        user_message="ahoj",
        actor_id="u1",
    )

    assert spy.calls == ["search_companies"]
