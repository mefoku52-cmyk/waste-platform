"""Regresné testy produkčnej cesty: get_agent_orchestrator + project tools.

Kryje: registráciu v skutočnej DI ceste (admin vs non-admin), end-to-end
volanie cez AgentOrchestrator s policy + permission + audit, odmietnutie
traversal aj nepovolených mien, a že OpenList NIE JE zapojený.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.domain.policy.policy_context import PolicyContext
from app.modules.agent_platform.domain.policy.policy_decision import PolicyOutcome
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse
from app.modules.agent_platform.presentation import dependencies


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="admin-1",
        email="platform-admin@test.local",
        roleCodes=["platform_admin"],
        memberships=[],
    )


def _regular_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="user-1",
        email="regular@test.local",
        roleCodes=["user"],
        memberships=[],
    )


class _FakeSession:
    """Stačí na konštrukciu repo/handlerov — žiadny IO sa pri buildi nevolá."""


class _ScriptedGateway:
    """Fake model: 1. odpoveď = tool_call, 2. odpoveď = hotovo."""

    def __init__(self, tool_name: str, arguments: dict[str, Any]) -> None:
        self._tool_name = tool_name
        self._arguments = arguments
        self.calls = 0

    def provider_name(self) -> str:
        return "fake"

    async def generate(self, request) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            import json

            return ModelResponse(
                request_id=request.request_id,
                text="",
                finish_reason="tool_calls",
                tool_calls=(
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": self._tool_name,
                            "arguments": json.dumps(self._arguments),
                        },
                    },
                ),
            )
        return ModelResponse(
            request_id=request.request_id,
            text="Hotovo.",
            finish_reason="stop",
            tool_calls=(),
        )


async def _build_orchestrator(user: SimpleNamespace) -> AgentOrchestrator:
    return await dependencies.get_agent_orchestrator(
        session=_FakeSession(),  # type: ignore[arg-type]
        current_user=user,
    )


def _schema_names(orch: AgentOrchestrator) -> set[str]:
    return {s["function"]["name"] for s in orch._tool_schemas}


# ─── registrácia v skutočnej produkčnej ceste ───────────────────────────────


async def test_admin_gets_project_tools_in_production_path() -> None:
    orch = await _build_orchestrator(_admin_user())
    assert "project_read_file" in orch._tool_handlers
    assert "project_list_dir" in orch._tool_handlers
    assert orch._tool_scopes["project_read_file"] == ("admin", "read")
    assert orch._tool_scopes["project_list_dir"] == ("admin", "read")
    names = _schema_names(orch)
    assert {"project_read_file", "project_list_dir"} <= names


async def test_non_admin_does_not_get_project_tools() -> None:
    orch = await _build_orchestrator(_regular_user())
    assert "project_read_file" not in orch._tool_handlers
    assert "project_list_dir" not in orch._tool_handlers
    names = _schema_names(orch)
    assert "project_read_file" not in names
    assert "project_list_dir" not in names


async def test_non_admin_policy_denies_project_tool() -> None:
    """Ani keby model zavolal project_read_file, policy ho musí odmietnuť."""
    orch = await _build_orchestrator(_regular_user())
    assert orch._policy is not None
    decision = await orch._policy.decide(
        PolicyContext(
            actor_id="user-1",
            actor_type="user",
            agent_id=None,
            action="tool.call",
            target=None,
            tool_name="project_read_file",
            risk_level=None,
            attributes={},
        )
    )
    assert decision.outcome == PolicyOutcome.DENY


async def test_existing_user_tools_preserved_for_non_admin() -> None:
    """Zmena nesmie obrať bežných userov o existujúce nástroje."""
    orch = await _build_orchestrator(_regular_user())
    for name in ("search_companies", "search_listings", "get_my_listings"):
        assert name in orch._tool_handlers
    assert "get_platform_stats" not in orch._tool_handlers


async def test_admin_keeps_admin_tools_and_project_tools() -> None:
    orch = await _build_orchestrator(_admin_user())
    assert "get_platform_stats" in orch._tool_handlers
    assert "search_companies" in orch._tool_handlers


async def test_openlist_not_wired_in_production() -> None:
    """OpenList zostáva vypnutý — nesmie byť v schémach ani handlroch."""
    orch = await _build_orchestrator(_admin_user())
    names = _schema_names(orch)
    assert not any(n.startswith("external.openlist") for n in names)
    assert not any(n.startswith("external.openlist") for n in orch._tool_handlers)


# ─── end-to-end: model tool_call → handler → audit ──────────────────────────


async def test_project_read_executes_end_to_end_with_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audit_calls: list[dict[str, str]] = []

    async def _fake_write_audit(**kwargs: Any) -> None:
        audit_calls.append({"action": kwargs["action"], "details": kwargs.get("details") or ""})

    monkeypatch.setattr(dependencies, "write_audit", _fake_write_audit)

    async def _fake_record(self: Any, record: Any) -> None:
        audit_calls.append({"action": str(record.action), "details": str(record.reason)})

    from app.modules.agent_platform.application.audit import audit_service

    monkeypatch.setattr(audit_service.DefaultAuditService, "record", _fake_record)

    orch = await _build_orchestrator(_admin_user())
    orch._gateway = _ScriptedGateway("project_read_file", {"path": "pyproject.toml"})

    result = await orch.respond(
        system_prompt="sys",
        user_message="prečítaj pyproject.toml",
        actor_id="admin-1",
        actor_type="admin",
    )

    assert result.tool_calls
    assert result.tool_calls[0]["name"] == "project_read_file"
    # Aspoň jeden audit sink musel zaznamenať execúciu.
    assert any("EXECUTE" in c["action"] or "executed" in c["action"] for c in audit_calls)


async def test_project_read_traversal_fails_and_is_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audit_calls: list[str] = []

    async def _fake_write_audit(**kwargs: Any) -> None:
        audit_calls.append(kwargs["action"])

    monkeypatch.setattr(dependencies, "write_audit", _fake_write_audit)

    orch = await _build_orchestrator(_admin_user())
    orch._gateway = _ScriptedGateway("project_read_file", {"path": "../../etc/passwd"})

    await orch.respond(
        system_prompt="sys",
        user_message="prečítaj /etc/passwd",
        actor_id="admin-1",
        actor_type="admin",
    )

    assert "agent.tool.failed" in audit_calls


async def test_unknown_tool_name_is_denied_by_policy_and_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audit_calls: list[str] = []

    async def _fake_write_audit(**kwargs: Any) -> None:
        audit_calls.append(kwargs["action"])

    monkeypatch.setattr(dependencies, "write_audit", _fake_write_audit)

    orch = await _build_orchestrator(_admin_user())
    orch._gateway = _ScriptedGateway("shell_execute", {"cmd": "rm -rf /"})

    await orch.respond(
        system_prompt="sys",
        user_message="vykonaj príkaz",
        actor_id="admin-1",
        actor_type="admin",
    )

    assert "agent.tool.denied_by_policy" in audit_calls


async def test_openlist_tool_call_denied_even_for_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model, ktorý si vymyslí OpenList tool, musí dostať denied_by_policy."""
    audit_calls: list[str] = []

    async def _fake_write_audit(**kwargs: Any) -> None:
        audit_calls.append(kwargs["action"])

    monkeypatch.setattr(dependencies, "write_audit", _fake_write_audit)

    orch = await _build_orchestrator(_admin_user())
    orch._gateway = _ScriptedGateway("external.openlist.list", {"path": "."})

    await orch.respond(
        system_prompt="sys",
        user_message="zoznam cez openlist",
        actor_id="admin-1",
        actor_type="admin",
    )

    assert "agent.tool.denied_by_policy" in audit_calls
