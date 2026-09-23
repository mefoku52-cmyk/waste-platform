"""Phase 4.1 dispatcher tests."""

import pytest

from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.agent_platform.infrastructure.tools.cmep_tool_dispatcher import (
    CMEPToolDispatcher,
)
from app.modules.agent_platform.infrastructure.tools.dispatcher_tool_executor import (
    DispatcherToolExecutor,
)
from app.modules.agent_platform.infrastructure.tools.in_memory_tool_handler_registry import (
    InMemoryToolHandlerRegistry,
)
from app.modules.agent_platform.infrastructure.tools.in_memory_tool_registry import (
    InMemoryToolRegistry,
)
from app.modules.agent_platform.infrastructure.tools.registry_tool_guard import (
    RegistryToolGuard,
)


class Definition:
    def __init__(self, name, *, enabled=True, allowed_actor_types=None):
        self.name = name
        self.enabled = enabled
        self.allowed_actor_types = allowed_actor_types


class Handler:
    def __init__(self):
        self.calls = 0

    async def handle(self, request):
        self.calls += 1
        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={"ok": True},
        )


def build():
    registry = InMemoryToolRegistry()
    registry.register(
        Definition(
            "cmep.company.search",
            allowed_actor_types={"user", "admin", "ai"},
        )
    )

    handlers = InMemoryToolHandlerRegistry()
    handler = Handler()
    handlers.register("cmep.company.search", handler)

    dispatcher = CMEPToolDispatcher(
        registry=registry,
        guard=RegistryToolGuard(registry),
        handlers=handlers,
    )

    return DispatcherToolExecutor(dispatcher), handler


@pytest.mark.asyncio
async def test_registered_tool_executes():
    executor, handler = build()

    result = await executor.execute(
        ToolRequest(
            request_id="d-1",
            tool_name="cmep.company.search",
            actor_id="u-1",
            actor_type="user",
            arguments={"q": "paper"},
            reason="test",
        )
    )

    assert result.success is True
    assert result.data == {"ok": True}
    assert handler.calls == 1


@pytest.mark.asyncio
async def test_unknown_tool_is_blocked():
    executor, _ = build()

    result = await executor.execute(
        ToolRequest(
            request_id="d-2",
            tool_name="unknown.tool",
            actor_id="u-1",
            actor_type="user",
            arguments={},
            reason="test",
        )
    )

    assert result.success is False
    assert result.error_code == "unknown_tool"


@pytest.mark.asyncio
async def test_wrong_actor_is_blocked_before_handler():
    executor, handler = build()

    result = await executor.execute(
        ToolRequest(
            request_id="d-3",
            tool_name="cmep.company.search",
            actor_id="service-1",
            actor_type="system",
            arguments={},
            reason="test",
        )
    )

    assert result.success is False
    assert result.error_code == "actor_not_allowed"
    assert handler.calls == 0


@pytest.mark.asyncio
async def test_request_identity_is_preserved():
    executor, _ = build()

    result = await executor.execute(
        ToolRequest(
            request_id="d-4",
            tool_name="cmep.company.search",
            actor_id="u-1",
            actor_type="user",
            arguments={},
            reason="test",
        )
    )

    assert result.request_id == "d-4"
    assert result.tool_name == "cmep.company.search"
