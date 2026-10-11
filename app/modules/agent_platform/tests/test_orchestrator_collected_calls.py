"""N1 regression: only tools that actually pass policy + permission and have an
executed handler may appear in the final ``OrchestrationResult.tool_calls``.

A denied, unmapped or unknown tool must never surface as an executed call — while
legitimately allowed server tools and client actions must still show up.
"""

from __future__ import annotations

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse
from app.modules.agent_platform.infrastructure.permission.actor_tool_permission_engine import (
    ActorToolPermissionEngine,
)
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
    """First turn requests one tool call, second turn answers with text."""

    def __init__(self, tool_name: str, args: str = "{}") -> None:
        self._tool_name = tool_name
        self._args = args
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
                        "function": {"name": self._tool_name, "arguments": self._args},
                    },
                ),
            )
        return ModelResponse(
            request_id=request.request_id,
            text="Hotovo.",
            finish_reason="stop",
            tool_calls=(),
        )


def _engine(
    *,
    actors: frozenset[str] = frozenset({"user", "admin"}),
    scopes: frozenset[tuple[str, str]] = frozenset({("companies", "search")}),
) -> ActorToolPermissionEngine:
    return ActorToolPermissionEngine(allowed_actor_types=actors, allowed_scopes=scopes)


async def test_allowed_server_tool_is_recorded_as_executed() -> None:
    gateway = _FakeGateway("search_companies")
    spy = _SpyHandler()
    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        model="test",
        policy=AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_companies"})),
        permission=_engine(),
        tool_scopes={"search_companies": ("companies", "search")},
    )

    result = await orch.respond(system_prompt="sys", user_message="ahoj", actor_id="u1")

    assert spy.calls == ["search_companies"], "Allowed tool must execute"
    names = [tc["name"] for tc in result.tool_calls]
    assert names == ["search_companies"], "Executed tool must appear in tool_calls"
    assert result.tool_calls[0]["id"] == "call_1"
    assert result.text == "Hotovo."


async def test_policy_denied_tool_is_not_recorded() -> None:
    gateway = _FakeGateway("secret_tool")
    spy = _SpyHandler()
    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"secret_tool": spy},
        model="test",
        policy=AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_companies"})),
    )

    result = await orch.respond(system_prompt="sys", user_message="ahoj", actor_id="u1")

    assert spy.calls == [], "Denied tool must not execute"
    assert result.tool_calls == (), "Denied tool must not appear as an executed call"
    assert result.text == "Hotovo."


async def test_unknown_tool_without_handler_is_not_recorded() -> None:
    # Policy allows the name, but no handler is wired for it → unknown tool.
    gateway = _FakeGateway("ghost_tool")
    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={},
        model="test",
        policy=AllowlistPolicyEngine(allowed_tool_names=frozenset({"ghost_tool"})),
    )

    result = await orch.respond(system_prompt="sys", user_message="ahoj", actor_id="u1")

    assert result.tool_calls == (), "Handler-less (unknown) tool must not be recorded"
    assert result.text == "Hotovo."


async def test_unmapped_scope_tool_is_not_recorded() -> None:
    gateway = _FakeGateway("search_companies")
    spy = _SpyHandler()
    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        model="test",
        permission=_engine(),
        tool_scopes={},  # scope not mapped → denied before execution
    )

    result = await orch.respond(system_prompt="sys", user_message="ahoj", actor_id="u1")

    assert spy.calls == []
    assert result.tool_calls == (), "Scope-unmapped tool must not be recorded"


async def test_permission_denied_tool_is_not_recorded() -> None:
    gateway = _FakeGateway("search_companies")
    spy = _SpyHandler()
    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        model="test",
        permission=_engine(actors=frozenset({"admin"})),  # user not allowed
        tool_scopes={"search_companies": ("companies", "search")},
    )

    result = await orch.respond(
        system_prompt="sys", user_message="ahoj", actor_id="u1", actor_type="user"
    )

    assert spy.calls == []
    assert result.tool_calls == (), "Permission-denied tool must not be recorded"


async def test_client_action_is_recorded_after_policy() -> None:
    gateway = _FakeGateway("navigate", args='{"url": "/dashboard/listings/new"}')
    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={},
        model="test",
        policy=AllowlistPolicyEngine(allowed_tool_names=frozenset({"navigate"})),
        permission=_engine(scopes=frozenset({("client", "action")})),
        tool_scopes={"navigate": ("client", "action")},
        client_tool_names=frozenset({"navigate"}),
    )

    result = await orch.respond(system_prompt="sys", user_message="ahoj", actor_id="u1")

    names = [tc["name"] for tc in result.tool_calls]
    assert names == ["navigate"], "Allowed client action must still be recorded"
