"""Test deduplication of identical server tool calls within a turn."""

from __future__ import annotations

import json

import pytest

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.domain.permission.permission_decision import (
    PermissionDecision,
    PermissionOutcome,
)
from app.modules.agent_platform.domain.policy.policy_decision import (
    PolicyDecision,
    PolicyOutcome,
)
from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse


class _SeqGateway(ModelGateway):
    def __init__(self, responses: list[ModelResponse]):
        self._responses = list(responses)
        self.calls = 0

    def provider_name(self) -> str:
        return "stub"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        resp = self._responses[self.calls]
        self.calls += 1
        return resp


class _PolicyAllow:
    async def decide(self, ctx):
        return PolicyDecision(outcome=PolicyOutcome.ALLOW, rule_id="allow", reason="ok")


class _PermAllow:
    async def authorize(self, req):
        return PermissionDecision(
            outcome=PermissionOutcome.ALLOWED,
            policy_rule_id="perm-allow",
            reason="ok",
        )


class _CountHandler:
    def __init__(self):
        self.count = 0

    async def handle(self, req: ToolRequest) -> ToolResult:
        self.count += 1
        return ToolResult(
            request_id=req.request_id,
            tool_name=req.tool_name,
            success=True,
            data={"ok": True},
        )


def _tool_call(name: str, args: dict, call_id: str):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


@pytest.mark.asyncio
async def test_duplicate_server_tool_calls_executed_once():
    handler = _CountHandler()
    gw = _SeqGateway(
        [
            ModelResponse(
                request_id="r1",
                text="",
                finish_reason="tool_calls",
                tool_calls=(_tool_call("search_listings", {"q": "pet"}, "c1"),),
                provider_metadata={},
            ),
            ModelResponse(
                request_id="r2",
                text="",
                finish_reason="tool_calls",
                tool_calls=(
                    _tool_call("search_listings", {"q": "pet"}, "c2"),
                    _tool_call("search_listings", {"q": "pet"}, "c3"),
                ),
                provider_metadata={},
            ),
            ModelResponse(
                request_id="r3",
                text="odpoved",
                finish_reason="stop",
                tool_calls=(),
                provider_metadata={},
            ),
        ]
    )
    orch = AgentOrchestrator(
        gateway=gw,
        tool_schemas=(),
        tool_handlers={"search_listings": handler},
        policy=_PolicyAllow(),
        permission=_PermAllow(),
        tool_scopes={"search_listings": ("listing", "read")},
        model="m",
    )
    res = await orch.respond(
        system_prompt="s",
        user_message="u",
        actor_id="u1",
        actor_type="user",
    )
    assert handler.count == 1
    assert len(res.tool_calls) == 1
