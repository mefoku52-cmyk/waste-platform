"""Permission gate tests – DENIED must not call handler."""

from __future__ import annotations

import pytest

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.domain.permission.permission_decision import (
    PermissionOutcome,
)
from app.modules.agent_platform.domain.permission.permission_request import (
    PermissionRequest,
)
from app.modules.agent_platform.domain.permission.permission_scope import (
    PermissionScope,
)
from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse
from app.modules.agent_platform.infrastructure.permission.actor_tool_permission_engine import (
    ActorToolPermissionEngine,
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


def _engine(
    *,
    actors: frozenset[str] = frozenset({"user", "admin"}),
    scopes: frozenset[tuple[str, str]] = frozenset({("companies", "search")}),
) -> ActorToolPermissionEngine:
    return ActorToolPermissionEngine(
        allowed_actor_types=actors,
        allowed_scopes=scopes,
    )


def _req(
    *,
    actor_id: str = "u1",
    actor_type: str = "user",
    resource: str = "companies",
    action: str = "search",
) -> PermissionRequest:
    return PermissionRequest(
        request_id="r1",
        actor_id=actor_id,
        actor_type=actor_type,
        scope=PermissionScope(resource=resource, action=action),
        reason="test",
    )


@pytest.mark.asyncio
async def test_permission_allows_user_for_read_tool() -> None:
    decision = await _engine().authorize(_req())
    assert decision.outcome == PermissionOutcome.ALLOWED


@pytest.mark.asyncio
async def test_permission_denies_unknown_actor_type() -> None:
    decision = await _engine().authorize(_req(actor_type="guest"))
    assert decision.outcome == PermissionOutcome.DENIED
    assert decision.policy_rule_id == "permission.unknown_actor_type"


def test_permission_request_rejects_missing_actor() -> None:
    """Domain enforces actor_id at construction: empty actor cannot reach the engine."""
    with pytest.raises(ValueError):
        _req(actor_id="")


@pytest.mark.asyncio
async def test_permission_denies_scope_outside_allowlist() -> None:
    decision = await _engine().authorize(_req(resource="payments", action="charge"))
    assert decision.outcome == PermissionOutcome.DENIED
    assert decision.policy_rule_id == "permission.scope_not_allowed"


@pytest.mark.asyncio
async def test_orchestrator_denies_when_permission_denies() -> None:
    gateway = _FakeGateway(tool_name="search_companies")
    spy = _SpyHandler()
    engine = _engine(actors=frozenset({"admin"}))

    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        model="test",
        permission=engine,
        tool_scopes={"search_companies": ("companies", "search")},
    )

    await orch.respond(
        system_prompt="sys",
        user_message="ahoj",
        actor_id="u1",
        actor_type="user",
    )

    assert spy.calls == [], "Handler must not be called when permission denies"


@pytest.mark.asyncio
async def test_orchestrator_calls_handler_when_permission_allows() -> None:
    gateway = _FakeGateway(tool_name="search_companies")
    spy = _SpyHandler()
    engine = _engine()

    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        model="test",
        permission=engine,
        tool_scopes={"search_companies": ("companies", "search")},
    )

    await orch.respond(
        system_prompt="sys",
        user_message="ahoj",
        actor_id="u1",
        actor_type="user",
    )

    assert spy.calls == ["search_companies"]


@pytest.mark.asyncio
async def test_orchestrator_denies_when_tool_scope_missing() -> None:
    gateway = _FakeGateway(tool_name="search_companies")
    spy = _SpyHandler()
    engine = _engine()

    orch = AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        model="test",
        permission=engine,
        tool_scopes={},
    )

    await orch.respond(
        system_prompt="sys",
        user_message="ahoj",
        actor_id="u1",
        actor_type="user",
    )

    assert spy.calls == []
