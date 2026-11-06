import socket

import httpx
import pytest

from app.modules.mcp_client import (
    McpProtocolError,
    McpServerConfig,
    McpTransportError,
    StreamableHttpTransport,
    validate_endpoint,
)


@pytest.fixture
def public_dns(monkeypatch):
    def fake_getaddrinfo(host, port, **kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", port),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


def config(**overrides):
    values = {
        "endpoint": "https://mcp.example.com",
        "allowed_hosts": ("mcp.example.com",),
    }
    values.update(overrides)
    return McpServerConfig(**values)


@pytest.mark.asyncio
async def test_request_json_response(public_dns):
    async def handler(request):
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"ok": True},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = StreamableHttpTransport(config(), http_client=client)

    try:
        result = await transport.request("tools/list")
        assert result == {"ok": True}
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_request_sse_response(public_dns):
    async def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=('data: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n\n'),
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = StreamableHttpTransport(config(), http_client=client)

    try:
        result = await transport.request("tools/list")
        assert result == {"ok": True}
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_request_enforces_response_limit(public_dns):
    async def handler(request):
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"payload": "x" * 1000},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = StreamableHttpTransport(
        config(max_response_bytes=64),
        http_client=client,
    )

    try:
        with pytest.raises(McpTransportError, match="size limit"):
            await transport.request("tools/list")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_notify_rejects_response_body(public_dns):
    async def handler(request):
        return httpx.Response(200, content=b"unexpected")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = StreamableHttpTransport(config(), http_client=client)

    try:
        with pytest.raises(McpTransportError, match="body"):
            await transport.notify("notifications/initialized")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_protocol_error_preserves_metadata(public_dns):
    async def handler(request):
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32000,
                    "message": "Remote failure",
                    "data": {"reason": "test"},
                },
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = StreamableHttpTransport(config(), http_client=client)

    try:
        with pytest.raises(McpProtocolError) as captured:
            await transport.request("tools/list")

        assert captured.value.code == -32000
        assert captured.value.data == {"reason": "test"}
    finally:
        await client.aclose()


def test_private_dns_is_rejected(monkeypatch):
    def private_dns(host, port, **kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", port),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", private_dns)

    with pytest.raises(ValueError, match="non-public"):
        validate_endpoint(config())


def test_endpoint_allowlist_is_enforced():
    cfg = config(
        endpoint="https://other.example.com",
    )

    with pytest.raises(ValueError, match="allowlist"):
        validate_endpoint(cfg, resolve_dns=False)


def test_token_header_rejects_newlines(public_dns):
    transport = StreamableHttpTransport(
        config(),
        token_provider=lambda: "token\r\nInjected: yes",
    )

    with pytest.raises(ValueError, match="header characters"):
        transport._headers()


def test_max_response_bytes_is_validated():
    with pytest.raises(ValueError, match="max_response_bytes"):
        config(max_response_bytes=0)

    with pytest.raises(ValueError, match="max_response_bytes"):
        config(max_response_bytes=20 * 1024 * 1024)


def test_disabled_transport_configuration():
    cfg = config(enabled=False)
    assert cfg.enabled is False
