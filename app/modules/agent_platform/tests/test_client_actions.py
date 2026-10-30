"""Regression tests for frontend client actions.

Covers:
* the client-action argument validator (allowed, unknown, unsafe args);
* orchestrator hand-off: valid actions reach the frontend, invalid/denied ones
  never do, and the audit outcome is correct;
* the client-action allowlist stays consistent between the schema, the
  orchestrator wiring and the chat router hand-off.
"""

from __future__ import annotations

import pytest

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse
from app.modules.agent_platform.infrastructure.permission.actor_tool_permission_engine import (
    ActorToolPermissionEngine,
)
from app.modules.agent_platform.infrastructure.policy.allowlist_policy_engine import (
    AllowlistPolicyEngine,
)
from app.modules.agent_platform.infrastructure.tools.client_action_validation import (
    validate_client_action,
)
from app.modules.agent_platform.infrastructure.tools.tool_schemas import (
    CLIENT_ACTION_NAMES,
)


class _Gateway:
    def __init__(self, calls: list[tuple[str, str]]) -> None:
        self._calls = list(calls)
        self._index = 0

    def provider_name(self) -> str:
        return "fake"

    async def generate(self, request) -> ModelResponse:
        if self._index < len(self._calls):
            name, arguments = self._calls[self._index]
            self._index += 1
            return ModelResponse(
                request_id=request.request_id,
                text="",
                finish_reason="tool_calls",
                tool_calls=(
                    {
                        "id": f"call_{self._index}",
                        "type": "function",
                        "function": {"name": name, "arguments": arguments},
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
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def __call__(
        self,
        actor_id: str,
        tool_name: str,
        outcome: str,
        duration_s: float,
    ) -> None:
        self.calls.append((actor_id, tool_name, outcome))


def _client_scopes() -> dict[str, tuple[str, str]]:
    return dict.fromkeys(CLIENT_ACTION_NAMES, ("client", "action"))


def _orchestrator(gateway: _Gateway, audit: _AuditSpy) -> AgentOrchestrator:
    scopes = _client_scopes()
    return AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={},
        model="test",
        policy=AllowlistPolicyEngine(allowed_tool_names=CLIENT_ACTION_NAMES),
        permission=ActorToolPermissionEngine(
            allowed_actor_types=frozenset({"user", "admin"}),
            allowed_scopes=frozenset(scopes.values()),
        ),
        tool_scopes=scopes,
        audit=audit,
        client_tool_names=CLIENT_ACTION_NAMES,
    )


# ─── Validator ────────────────────────────────────────────────────────────


def test_validator_rejects_unknown_action() -> None:
    result = validate_client_action("not_a_client_action", {})
    assert result.valid is False
    assert result.error_code == "client_unknown_action"


def test_validator_navigate_blocks_external_paths() -> None:
    for url in (
        "https://evil.example",
        "//evil.example",
        "/../etc/passwd",
        "/dashboard/..%2F..%2Fetc",
        "/dashboard\\evil",
        "/dashboard:8080/x",
    ):
        result = validate_client_action("navigate", {"url": url})
        assert result.valid is False, url


def test_validator_navigate_allows_internal_path() -> None:
    result = validate_client_action("navigate", {"url": "/dashboard/listings/new"})
    assert result.valid is True
    assert result.arguments["url"] == "/dashboard/listings/new"


def test_validator_open_listing_requires_safe_id() -> None:
    assert validate_client_action("open_listing", {}).valid is False
    assert validate_client_action("open_listing", {"listing_id": "../secret"}).valid is False
    result = validate_client_action("open_listing", {"listing_id": "abc-123_def"})
    assert result.valid is True


def test_validator_fill_form_field_allowlist_and_types() -> None:
    assert validate_client_action("fill_form_field", {"field": "title", "value": "x"}).valid
    assert validate_client_action("fill_form_field", {"field": "root", "value": "x"}).valid is False
    assert (
        validate_client_action("fill_form_field", {"field": "title", "value": {"a": 1}}).valid
        is False
    )
    assert (
        validate_client_action("fill_form_field", {"field": "quantity", "value": "abc"}).valid
        is False
    )
    assert validate_client_action("fill_form_field", {"field": "quantity", "value": 5}).valid


def test_validator_fill_form_field_company_fields() -> None:
    """Company-form fields are fillable; logoUrl is not (no simple input)."""
    for field, value in (
        ("legalName", "Acme s.r.o."),
        ("tradingName", "Acme"),
        ("registrationNumber", "54642442"),
        ("vatIdentifier", "SK2020123456"),
        ("companyType", "seller"),
        ("countryCode", "SK"),
        ("addressLine1", "Hlavna 1"),
        ("city", "Bratislava"),
        ("postalCode", "81101"),
        ("email", "a@b.sk"),
        ("phone", "+421900000000"),
        ("entityType", "company"),
    ):
        assert validate_client_action("fill_form_field", {"field": field, "value": value}).valid, (
            field
        )

    # Numeric-only rule must not apply to string identifiers like postal codes.
    assert validate_client_action(
        "fill_form_field", {"field": "postalCode", "value": "81101"}
    ).valid
    # logoUrl is deliberately NOT fillable.
    assert (
        validate_client_action("fill_form_field", {"field": "logoUrl", "value": "x"}).valid is False
    )
    # highlight honours the same allowlist.
    assert validate_client_action("highlight_field", {"field": "legalName"}).valid
    assert validate_client_action("highlight_field", {"field": "logoUrl"}).valid is False


def test_validator_show_toast_level() -> None:
    assert validate_client_action("show_toast", {"message": "hi"}).valid
    assert validate_client_action("show_toast", {"message": "hi", "level": "warning"}).valid
    assert validate_client_action("show_toast", {"message": "hi", "level": "loud"}).valid is False
    assert validate_client_action("show_toast", {"message": ""}).valid is False


def test_validator_show_toast_strips_unknown_arguments() -> None:
    result = validate_client_action("show_toast", {"message": "hi", "injected": "x"})
    assert result.valid is True
    assert set(result.arguments) == {"message", "level"}


def test_validator_new_no_arg_navigations() -> None:
    """FIX 4: the added navigation actions are valid and argument-free."""
    for name in (
        "open_new_company",
        "open_documents",
        "open_new_document",
        "open_chat",
        "open_settings",
        "open_admin",
    ):
        result = validate_client_action(name, {"junk": "x"})
        assert result.valid is True, name
        assert result.arguments == {}, name


def test_open_admin_is_admin_only_schema() -> None:
    """open_admin is offered only to admins but still allowlisted."""
    from app.modules.agent_platform.infrastructure.tools.tool_schemas import (
        ADMIN_CLIENT_ACTION_SCHEMAS,
        CLIENT_ACTION_SCHEMAS,
    )

    regular = {s["function"]["name"] for s in CLIENT_ACTION_SCHEMAS}
    admin_only = {s["function"]["name"] for s in ADMIN_CLIENT_ACTION_SCHEMAS}
    assert "open_admin" in admin_only
    assert "open_admin" not in regular
    assert "open_admin" in CLIENT_ACTION_NAMES
    for name in ("open_new_company", "open_documents", "open_chat", "open_settings"):
        assert name in regular


# ─── Orchestrator hand-off ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_valid_client_action_is_handed_to_frontend() -> None:
    audit = _AuditSpy()
    orch = _orchestrator(_Gateway([("open_dashboard", "{}")]), audit)

    result = await orch.respond(system_prompt="s", user_message="u", actor_id="a1")

    assert [tc["name"] for tc in result.tool_calls] == ["open_dashboard"]
    assert result.tool_calls[0]["arguments"] == {}
    assert audit.calls == [("a1", "open_dashboard", "dispatched_to_client")]


@pytest.mark.asyncio
async def test_invalid_client_arguments_are_not_dispatched() -> None:
    audit = _AuditSpy()
    orch = _orchestrator(_Gateway([("open_listing", '{"listing_id": "../secret"}')]), audit)

    result = await orch.respond(system_prompt="s", user_message="u", actor_id="a1")

    assert all(tc["name"] != "open_listing" for tc in result.tool_calls)
    assert ("a1", "open_listing", "client_action_invalid_arguments") in audit.calls


@pytest.mark.asyncio
async def test_unknown_action_is_denied_by_policy() -> None:
    audit = _AuditSpy()
    orch = _orchestrator(_Gateway([("evil_client_action", "{}")]), audit)

    await orch.respond(system_prompt="s", user_message="u", actor_id="a1")

    assert audit.calls == [("a1", "evil_client_action", "denied_by_policy")]


# ─── Wiring / hand-off consistency ──────────────────────────────────────────


def test_dependencies_client_scopes_cover_all_action_names() -> None:
    from app.modules.agent_platform.presentation.dependencies import (
        client_action_scopes,
    )

    scopes = client_action_scopes()
    assert set(scopes) == set(CLIENT_ACTION_NAMES)
    assert set(scopes.values()) == {("client", "action")}


def test_chat_router_client_names_match_schema() -> None:
    from app.modules.agent_platform.presentation import chat_router

    assert chat_router.CLIENT_TOOL_NAMES == CLIENT_ACTION_NAMES


def test_validator_accepts_safe_navigation_actions() -> None:
    for name in ("open_transport", "open_subscription", "open_marketplace"):
        result = validate_client_action(name, {"ignored": "argument"})
        assert result.valid is True, name
        assert result.arguments == {}, name

    assert "select_plan_ai" not in CLIENT_ACTION_NAMES
    assert "select_plan_ai_nav" not in CLIENT_ACTION_NAMES


def test_open_admin_client_action_is_server_authorized(monkeypatch) -> None:
    from app.modules.agent_platform.presentation import chat_router

    monkeypatch.setattr(chat_router, "is_platform_admin", lambda user: user == "admin")
    assert chat_router._client_action_allowed_for_user("open_admin", "user") is False
    assert chat_router._client_action_allowed_for_user("open_admin", "admin") is True
    assert chat_router._client_action_allowed_for_user("open_dashboard", "user") is True
