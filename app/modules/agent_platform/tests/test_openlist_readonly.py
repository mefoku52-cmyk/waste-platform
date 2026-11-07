"""Testy openlist_readonly modulu s MOCKS — žiadny reálny server ani údaje.

OpenList je zapojený do produkčnej ceste (iba pre platform admina). Tieto testy
overujú správanie pripraveného modulu: mapovanie chýb (nedostupný server,
timeout, neplatné prihlasovacie údaje, odpoveď príliš veľká), path traversal,
read-only allowlist, limit veľkosti odpovede a schémy. Nikdy nevolajú reálny
`127.0.0.1:5244`.
"""

from __future__ import annotations

import inspect
import json

import httpx
import pytest

from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.infrastructure.tools import openlist_readonly
from app.modules.agent_platform.infrastructure.tools.openlist_readonly import (
    OpenListGetHandler,
    OpenListListHandler,
    OpenListMcpClient,
    OpenListPathDenied,
    OpenListResponseTooLarge,
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


class _FakeStreamResponse:
    """Streaming fake HTTP response that tracks consumed chunks/bytes.

    Used to verify the client stops reading once the size limit is exceeded.
    Exposes aiter_raw(chunk_size=...) like httpx and records the request
    headers it was created with.
    """

    def __init__(
        self,
        status_code: int = 200,
        payload: dict | None = None,
        headers: dict | None = None,
        chunks: list[bytes] | None = None,
        request_headers: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = dict(headers or {})
        self.request_headers = dict(request_headers or {})
        if chunks is None:
            if payload is None:
                payload = {}
            chunks = [json.dumps(payload).encode("utf-8")]
        self.chunks = list(chunks)
        self.consumed_chunks = 0
        self.consumed_bytes = 0
        self.closed = False

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("POST", "http://mock"),
                response=httpx.Response(self.status_code),
            )

    async def aiter_raw(self, chunk_size: int = 64 * 1024):
        """Mirror httpx.Response.aiter_raw(chunk_size=...).

        chunk_size bounds the blocks yielded; it is NOT an absolute upper
        bound on temporary allocation inside the transport layer itself.
        """
        del chunk_size  # the fake yields whole chunks; chunk_size is accepted
        # for API compatibility with the real httpx call site.
        for chunk in self.chunks:
            self.consumed_chunks += 1
            self.consumed_bytes += len(chunk)
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


class _StreamResponseContext:
    def __init__(self, response: _FakeStreamResponse, exc: Exception | None) -> None:
        self._response = response
        self._exc = exc

    async def __aenter__(self):
        if self._exc is not None:
            raise self._exc
        return self._response

    async def __aexit__(self, *args):
        await self._response.aclose()
        return False


def _patch_streaming_httpx(
    monkeypatch,
    response: _FakeStreamResponse | None = None,
    exc: Exception | None = None,
) -> None:
    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            self._response = response
            self._exc = exc

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            if self._exc is not None:
                raise self._exc
            return self._response

        def stream(self, method, url, headers=None, json=None):
            if self._response is not None:
                self._response.request_headers = dict(headers or {})
            return _StreamResponseContext(self._response, self._exc)

    monkeypatch.setattr(openlist_readonly.httpx, "AsyncClient", _FakeAsyncClient)


async def test_invalid_credentials_map_to_auth_failed(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    _patch_streaming_httpx(monkeypatch, response=_FakeStreamResponse(status_code=401))
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_AUTH_FAILED"


async def test_timeout_maps_to_upstream_timeout(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    _patch_streaming_httpx(monkeypatch, exc=httpx.ConnectTimeout("mock timeout"))
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_TIMEOUT"


async def test_unavailable_server_maps_to_upstream_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    _patch_streaming_httpx(monkeypatch, exc=httpx.ConnectError("connection refused"))
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
    init = _FakeStreamResponse(
        payload={"jsonrpc": "2.0", "id": 1, "result": {}},
        headers={"Mcp-Session-Id": "sess-1"},
    )
    call = _FakeStreamResponse(
        payload={
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"structuredContent": {"content": [{"name": "app"}]}},
        }
    )
    responses = iter([init, _FakeStreamResponse(payload={}), call])

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def stream(self, method, url, headers=None, json=None):
            return _StreamResponseContext(next(responses), None)

    monkeypatch.setattr(openlist_readonly.httpx, "AsyncClient", _FakeAsyncClient)
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is True
    assert result.data == {"content": [{"name": "app"}]}


# ─── response-size limit (streaming enforcement) ─────────────────────────────


def _json_bytes_of_size(size: int) -> bytes:
    """Build a valid JSON-RPC response body of exactly `size` bytes."""
    prefix = '{"jsonrpc":"2.0","id":1,"result":{"data":"'
    suffix = '"}}'
    inner_len = size - len(prefix) - len(suffix)
    if inner_len < 0:
        raise ValueError(f"size {size} too small for JSON wrapper")
    inner = "X" * inner_len
    body = f"{prefix}{inner}{suffix}"
    data = body.encode("utf-8")
    assert len(data) == size, f"expected {size} bytes, got {len(data)}"
    return data


@pytest.mark.parametrize("method", ["initialize", "tools/call"])
async def test_oversized_initialization_and_call_rejected(monkeypatch, method) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    oversized = _json_bytes_of_size(101)
    response = _FakeStreamResponse(status_code=200, chunks=[oversized])
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    with pytest.raises(OpenListResponseTooLarge):
        await client._rpc(method, {"name": "x", "arguments": {}})
    # Nothing was consumed past the limit (Content-Length absent, streamed).
    assert response.consumed_chunks == 1  # the single oversized chunk triggered it
    assert response.consumed_bytes == 101


async def test_response_exactly_at_limit_is_accepted(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    body = _json_bytes_of_size(100)  # exactly at the limit
    response = _FakeStreamResponse(status_code=200, chunks=[body])
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    client._session_id = "sess-1"  # skip initialize, exercise tools/call only
    handler = OpenListListHandler(client)
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is True
    assert response.consumed_chunks == 1
    assert response.consumed_bytes == 100


async def test_response_one_byte_above_limit_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    body = _json_bytes_of_size(101)  # one byte above the limit
    response = _FakeStreamResponse(status_code=200, chunks=[body])
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    client._session_id = "sess-1"
    handler = OpenListListHandler(client)
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_RESPONSE_TOO_LARGE"
    assert response.consumed_bytes == 101


async def test_oversized_content_length_rejected_before_reading(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    # Content-Length claims 101 bytes; client must reject without consuming chunks.
    response = _FakeStreamResponse(
        status_code=200, chunks=[b"x" * 101], headers={"content-length": "101"}
    )
    _patch_streaming_httpx(monkeypatch, response=response)
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_RESPONSE_TOO_LARGE"
    assert response.consumed_chunks == 0
    assert response.consumed_bytes == 0


async def test_oversized_chunked_without_content_length_stopped_early(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    # No Content-Length header; two chunks of 60 bytes = 120 > 100.
    # A third huge chunk is queued but must never be consumed.
    chunks = [b"x" * 60, b"x" * 60, b"x" * 999999]
    response = _FakeStreamResponse(status_code=200, chunks=chunks)
    _patch_streaming_httpx(monkeypatch, response=response)
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_RESPONSE_TOO_LARGE"
    # Stopped early: 2 of 3 chunks consumed, never touched the 3rd.
    assert response.consumed_chunks == 2
    assert response.consumed_bytes == 120


async def test_multiple_chunks_exceeding_limit_cumulatively(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    chunks = [b"x" * 30, b"x" * 30, b"x" * 30, b"x" * 30, b"x" * 999999]
    response = _FakeStreamResponse(status_code=200, chunks=chunks)
    _patch_streaming_httpx(monkeypatch, response=response)
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_RESPONSE_TOO_LARGE"
    # Cumulative: 30*4 = 120 > 100 at the 4th chunk; 5th never consumed.
    assert response.consumed_chunks == 4
    assert response.consumed_bytes == 120


async def test_malformed_json_within_permitted_size(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    body = b"not valid json{"  # 15 bytes, within the limit, but not valid JSON
    response = _FakeStreamResponse(status_code=200, chunks=[body])
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    client._session_id = "sess-1"
    handler = OpenListListHandler(client)
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_UNAVAILABLE"
    assert response.consumed_chunks == 1
    assert response.consumed_bytes == 15


async def test_client_and_response_closed_after_rejection(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    client_exits = []
    response_exits = []

    class _TrackingClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            client_exits.append(True)
            return False

        def stream(self, method, url, headers=None, json=None):
            return _TrackingResponseContext()

    class _TrackingResponseContext:
        async def __aenter__(self):
            return _FakeStreamResponse(status_code=200, chunks=[b"x" * 101])

        async def __aexit__(self, *args):
            response_exits.append(True)
            return False

    monkeypatch.setattr(openlist_readonly.httpx, "AsyncClient", _TrackingClient)
    handler = OpenListListHandler(OpenListMcpClient())
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_RESPONSE_TOO_LARGE"
    assert client_exits == [True]
    assert response_exits == [True]


# ─── content-encoding / accept-encoding hardening ────────────────────────────


async def test_sends_accept_encoding_identity(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    body = _json_bytes_of_size(50)
    response = _FakeStreamResponse(status_code=200, chunks=[body])
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    client._session_id = "sess-1"
    handler = OpenListListHandler(client)
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is True
    assert response.request_headers.get("Accept-Encoding") == "identity"


@pytest.mark.parametrize("encoding", [None, "", "identity"])
async def test_missing_or_identity_content_encoding_accepted(monkeypatch, encoding) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    body = _json_bytes_of_size(50)
    headers = {}
    if encoding is not None:
        headers["content-encoding"] = encoding
    response = _FakeStreamResponse(status_code=200, chunks=[body], headers=headers)
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    client._session_id = "sess-1"
    handler = OpenListListHandler(client)
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is True


async def test_gzip_content_encoding_rejected(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    # Small compressed-on-the-wire body that would decompress past the limit.
    response = _FakeStreamResponse(
        status_code=200,
        chunks=[b"\x1f\x8b\x08\x00" + b"x" * 20],
        headers={"content-encoding": "gzip"},
    )
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    client._session_id = "sess-1"
    handler = OpenListListHandler(client)
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_RESPONSE_TOO_LARGE"
    # Rejected before consuming any chunks (header check).
    assert response.consumed_chunks == 0
    assert response.consumed_bytes == 0


async def test_deflate_content_encoding_rejected(monkeypatch) -> None:
    monkeypatch.setenv("OPENLIST_MCP_TOKEN", "mock-token-not-a-real-secret")
    monkeypatch.setattr(openlist_readonly, "_MAX_RESPONSE_BYTES", 100)
    response = _FakeStreamResponse(
        status_code=200,
        chunks=[b"x" * 10],
        headers={"content-encoding": "deflate"},
    )
    _patch_streaming_httpx(monkeypatch, response=response)
    client = OpenListMcpClient()
    client._session_id = "sess-1"
    handler = OpenListListHandler(client)
    result = await handler.handle(_req("external.openlist.list", {"path": "."}))
    assert result.success is False
    assert result.error_code == "UPSTREAM_RESPONSE_TOO_LARGE"
    assert response.consumed_chunks == 0
    assert response.consumed_bytes == 0


def test_uses_aiter_raw_with_chunk_size() -> None:
    """Verify the implementation calls aiter_raw(chunk_size=64*1024)."""
    source = inspect.getsource(openlist_readonly.OpenListMcpClient._rpc)
    assert "aiter_raw(chunk_size=64 * 1024)" in source


def test_openlist_imported_by_production_dependencies() -> None:
    """OpenList je importovaný a zapojený do produkčnej ceste (admin-only)."""
    source = inspect.getsource(
        __import__("app.modules.agent_platform.presentation.dependencies", fromlist=["x"])
    )
    assert "OpenListMcpClient" in source
    assert "OpenListListHandler" in source
    assert "OpenListGetHandler" in source
    assert "OPENLIST_READONLY_SCHEMAS" in source
    assert "external.openlist.list" in source
    assert "external.openlist.get" in source


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
