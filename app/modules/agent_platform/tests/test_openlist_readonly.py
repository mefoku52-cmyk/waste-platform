"""Testy openlist_readonly modulu s MOCKS — žiadny reálny server ani údaje.

OpenList NIE JE zapojený do produkčného agenta. Tieto testy overujú iba
správanie pripraveného modulu: mapovanie chýb (nedostupný server, timeout,
neplatné prihlasovacie údaje), path traversal, read-only allowlist a
schémy. Nikdy nevolajú reálny `127.0.0.1:5244`.
"""

from __future__ import annotations

import inspect

import httpx
import pytest

from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.infrastructure.tools import openlist_readonly
from app.modules.agent_platform.infrastructure.tools.openlist_readonly import (
    OpenListGetHandler,
    OpenListListHandler,
    OpenListMcpClient,
    OpenListPathDenied,
    resolve_openlist_path,
)
from app.modules.agent_platform.infrastructure.tools.tool_schemas import (
    OPENLIST_READONLY_NAMES,
    OPENLIST_READONLY_SCHEMAS,
)


def _req(tool_name: str, args: dict) -> ToolRequest:
    return ToolRequest(
        request_id="req-1",
        tool_name=tool_name,
        actor_id="admin-1",
        actor_type="admin",
        arguments=args,
        reason="test",
    )


# ─── path resolution ────────────────────────────────────────────────────────


def test_resolve_allows_relative_paths(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_ROOT", "/waste-platform")
    assert resolve_openlist_path("app/modules") == "/waste-platform/app/modules"
    assert resolve_openlist_path(".") == "/waste-platform"


@pytest.mark.parametrize(
    "evil",
    ["../etc", "a/../..", "/abs/path", "a\\b", "a\x00b", "a%2e%2e/b", "x" * 2000, ""],
)
def test_resolve_denies_traversal_and_abuse(evil: str) -> None:
    with pytest.raises(OpenListPathDenied):
        resolve_openlist_path(evil)


# ─── read-only allowlist na úrovni klienta ──────────────────────────────────


async def test_client_rejects_non_readonly_tools(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    client = OpenListMcpClient()
    with pytest.raises(PermissionError):
        await client.call_tool("openlist.fs.put", {"path": "x"})
    with pytest.raises(PermissionError):
        await client.call_tool("openlist.fs.remove", {"path": "x"})


async def test_client_requires_token(monkeypatch) -> None:
    monkeypatch.delenv("OPENLIST_MCP_TOKEN", raising=False)
    client = OpenListMcpClient()
    with pytest.raises(RuntimeError, match="OPENLIST_MCP_TOKEN missing"):
        await client._rpc("initialize", {})


# ─── httpx mock: 401 / timeout / nedostupný server ──────────────────────────


class _FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        payload: dict | None = None,
        headers: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("POST", "http://mock"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


def _patch_httpx(monkeypatch, response=None, exc: Exception | None = None) -> None:
    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            if exc is not None:
                raise exc
            return response

    monkeypatch.setattr(openlist_readonly.httpx, "AsyncClient", _FakeAsyncClient)


async def test_invalid_credentials_map_to_auth_failed(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    _patch_httpx(monkeypatch, response=_FakeResponse(status_code=401))
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_AUTH_FAILED"


async def test_timeout_maps_to_upstream_timeout(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    _patch_httpx(monkeypatch, exc=httpx.ConnectTimeout("mock timeout"))
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_TIMEOUT"


async def test_unavailable_server_maps_to_upstream_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    _patch_httpx(monkeypatch, exc=httpx.ConnectError("connection refused"))
    handler = OpenListGetHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.get", {"path": "app"}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_UNAVAILABLE"


async def test_missing_token_maps_to_upstream_unavailable(monkeypatch) -> None:
    monkeypatch.delenv("OPENLIST_MCP_TOKEN", raising=False)
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_UNAVAILABLE"


# ─── handler argument validation ────────────────────────────────────────────


async def test_list_rejects_unknown_args(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")

    class _NeverCalled:
        async def call_tool(self, *a, **k):
            raise AssertionError("handler must not reach upstream")

    handler = OpenListListHandler(_NeverCalled())  # type: ignore[arg-type]
    result = await handler.handle(_req("external.openlist.list", {"path": ".", "write": True}))
    assert result.success is False
    assert result.error_code == "invalid_arguments"


@pytest.mark.parametrize("args", [{"path": ".", "per_page": 101}, {"path": ".", "page": 0}])
async def test_list_rejects_bad_pagination(monkeypatch, args: dict) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    reached_upstream = False

    class _NeverCalled:
        async def call_tool(self, *a, **k):
            nonlocal reached_upstream
            reached_upstream = True
            raise AssertionError("handler must not reach upstream")

    handler = OpenListListHandler(_NeverCalled())  # type: ignore[arg-type]
    result = await handler.handle(_req("external.openlist.list", args))
    assert result.success is False
    assert reached_upstream is False


async def test_get_rejects_traversal(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")

    class _NeverCalled:
        async def call_tool(self, *a, **k):
            raise AssertionError("handler must not reach upstream")

    handler = OpenListGetHandler(_NeverCalled())  # type: ignore[arg-type]
    result = await handler.handle(_req("external.openlist.get", {"path": "../x"}))
    assert result.success is False
    assert result.error_code == "PATH_DENIED"


# ─── úspešná odpoveď (mock, structuredContent preference) ───────────────────


async def test_list_success_prefers_structured_content(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    init = _FakeResponse(
        payload={"jsonrpc": "2.0", "id": 1, "result": {}},
        headers={"Mcp-Session-Id": "sess-1"},
    )
    call = _FakeResponse(
        payload={
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"structuredContent": {"content": [{"name": "app"}]}},
        }
    )
    responses = iter([init, _FakeResponse(payload={}), call])

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            return next(responses)

    monkeypatch.setattr(openlist_readonly.httpx, "AsyncClient", _FakeAsyncClient)
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is True
    assert result.data == {"content": [{"name": "app"}]}


# ─── modul zostáva nezapojený + schémy obsahujú iba read operácie ──────────


def test_openlist_not_imported_by_production_dependencies() -> None:
    source = inspect.getsource(
        __import__("app.modules.agent_platform.presentation.dependencies", fromlist=["x"])
    )
    assert "openlist" not in source.lower()


def test_openlist_schemas_are_readonly_names() -> None:
    assert {
        "external.openlist.list",
        "external.openlist.get",
    } == OPENLIST_READONLY_NAMES
    assert len(OPENLIST_READONLY_SCHEMAS) == 2
    for schema in OPENLIST_READONLY_SCHEMAS:
        name = schema["function"]["name"]
        assert not any(
            verb in name for verb in ("write", "put", "remove", "delete", "move", "upload")
        )


def test_client_allowed_tools_are_readonly() -> None:
    assert {
        "openlist.fs.list",
        "openlist.fs.get",
    } == OpenListMcpClient._ALLOWED_TOOLS
