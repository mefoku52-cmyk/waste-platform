"""Admin tools tests – registered only for platform admins."""

from __future__ import annotations

import pytest

from app.modules.agent_platform.infrastructure.tools.tool_schemas import (
    build_admin_tools,
    build_default_tools,
)


def test_build_default_tools_has_no_admin_names() -> None:
    names = {t["function"]["name"] for t in build_default_tools()}
    assert "get_platform_stats" not in names
    assert "get_recent_activity" not in names
    assert "get_companies_with_tiers" not in names
    assert "get_my_company_context" not in names


def test_build_admin_tools_has_four_tools() -> None:
    tools = build_admin_tools()
    assert len(tools) == 4
    names = {t["function"]["name"] for t in tools}
    assert names == {
        "get_platform_stats",
        "get_recent_activity",
        "get_companies_with_tiers",
        "get_my_company_context",
    }


def test_admin_tools_are_flagged_read_only_in_description() -> None:
    for tool in build_admin_tools():
        desc = tool["function"]["description"]
        assert "READ-ONLY" in desc


@pytest.mark.asyncio
async def test_admin_handler_rejects_unknown_tool_name() -> None:
    from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
    from app.modules.agent_platform.infrastructure.tools.cmep_admin_tools import (
        CmepAdminToolsHandler,
    )

    handler = CmepAdminToolsHandler(session=None)  # type: ignore[arg-type]
    result = await handler.handle(
        ToolRequest(
            request_id="r1",
            tool_name="search_companies",
            actor_id="a1",
            actor_type="admin",
            arguments={},
            reason="test",
        )
    )
    assert result.success is False
    assert result.error_code == "unknown_admin_tool"


@pytest.mark.asyncio
async def test_admin_handler_rejects_invalid_arguments() -> None:
    from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
    from app.modules.agent_platform.infrastructure.tools.cmep_admin_tools import (
        CmepAdminToolsHandler,
    )

    handler = CmepAdminToolsHandler(session=None)  # type: ignore[arg-type]
    result = await handler.handle(
        ToolRequest(
            request_id="r1",
            tool_name="get_platform_stats",
            actor_id="a1",
            actor_type="admin",
            arguments={"unexpected": 1},
            reason="test",
        )
    )
    assert result.success is False
    assert result.error_code == "invalid_arguments"
