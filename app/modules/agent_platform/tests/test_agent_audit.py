"""Audit hook tests – each tool decision must call the audit callback."""

from __future__ import annotations

import pytest

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
    def __init__(self, *, success: bool = True) -> None:
        self.calls: list[str] = []
        self._success = success

    async def handle(self, request) -> ToolResult:
        self.calls.append(request.tool_name)
        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=self._success,
            data={"ok": True} if self._success else None,
            error_code=None if self._success else "fail_code",
            error_message=None if self._success else "fail_message",
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


class _AuditSpy:
    def __init__(self, *, raises: bool = False) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self._raises = raises

    async def __call__(
        self,
        actor_id: str,
        tool_name: str,
        outcome: str,
        duration_s: float,
    ) -> None:
        self.calls.append((actor_id, tool_name, outcome))
        if self._raises:
            raise RuntimeError("audit store down")


def _orch(
    *,
    tool_name: str,
    spy: _SpyHandler,
    audit: _AuditSpy | None,
    policy=None,
    permission=None,
    tool_scopes=None,
) -> AgentOrchestrator:
    return AgentOrchestrator(
        gateway=_FakeGateway(tool_name=tool_name),
        tool_schemas=(),
        tool_handlers={"search_companies": spy},
        model="test",
        policy=policy,
        permission=permission,
        tool_scopes=tool_scopes,
        audit=audit,
    )


@pytest.mark.asyncio
async def test_audit_called_on_success() -> None:
    spy = _SpyHandler()
    audit = _AuditSpy()
    orch = _orch(tool_name="search_companies", spy=spy, audit=audit)
    await orch.respond(system_prompt="s", user_message="u", actor_id="a1")
    assert audit.calls == [("a1", "search_companies", "executed")]
    assert spy.calls == ["search_companies"]


@pytest.mark.asyncio
async def test_audit_called_on_handler_failure() -> None:
    spy = _SpyHandler(success=False)
    audit = _AuditSpy()
    orch = _orch(tool_name="search_companies", spy=spy, audit=audit)
    await orch.respond(system_prompt="s", user_message="u", actor_id="a1")
    assert audit.calls == [("a1", "search_companies", "failed")]


@pytest.mark.asyncio
async def test_audit_called_on_policy_deny() -> None:
    spy = _SpyHandler()
    audit = _AuditSpy()
    policy = AllowlistPolicyEngine(allowed_tool_names=frozenset({"different_tool"}))
    orch = _orch(tool_name="search_companies", spy=spy, audit=audit, policy=policy)
    await orch.respond(system_prompt="s", user_message="u", actor_id="a1")
    assert audit.calls == [("a1", "search_companies", "denied_by_policy")]
    assert spy.calls == []


@pytest.mark.asyncio
async def test_audit_called_on_permission_deny() -> None:
    spy = _SpyHandler()
    audit = _AuditSpy()
    permission = ActorToolPermissionEngine(
        allowed_actor_types=frozenset({"admin"}),
        allowed_scopes=frozenset({("companies", "search")}),
    )
    orch = _orch(
        tool_name="search_companies",
        spy=spy,
        audit=audit,
        permission=permission,
        tool_scopes={"search_companies": ("companies", "search")},
    )
    await orch.respond(system_prompt="s", user_message="u", actor_id="a1", actor_type="user")
    assert audit.calls == [("a1", "search_companies", "denied_by_permission")]
    assert spy.calls == []


@pytest.mark.asyncio
async def test_audit_called_on_unknown_tool() -> None:
    spy = _SpyHandler()
    audit = _AuditSpy()
    orch = _orch(tool_name="not_in_handlers", spy=spy, audit=audit)
    await orch.respond(system_prompt="s", user_message="u", actor_id="a1")
    assert audit.calls == [("a1", "not_in_handlers", "tool_not_available")]
    assert spy.calls == []


@pytest.mark.asyncio
async def test_audit_failure_does_not_break_tool_call() -> None:
    spy = _SpyHandler()
    audit = _AuditSpy(raises=True)
    orch = _orch(tool_name="search_companies", spy=spy, audit=audit)
    await orch.respond(system_prompt="s", user_message="u", actor_id="a1")
    assert spy.calls == ["search_companies"]


@pytest.mark.asyncio
async def test_audit_optional() -> None:
    spy = _SpyHandler()
    orch = _orch(tool_name="search_companies", spy=spy, audit=None)
    await orch.respond(system_prompt="s", user_message="u", actor_id="a1")
    assert spy.calls == ["search_companies"]
