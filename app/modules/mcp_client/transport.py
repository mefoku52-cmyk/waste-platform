from __future__ import annotations

import asyncio
import ipaddress
import json
import socket
from collections.abc import Callable, Mapping
from urllib.parse import urlsplit

import httpx

from .errors import McpProtocolError, McpTransportError
from .models import McpServerConfig


def validate_endpoint(config: McpServerConfig, *, resolve_dns: bool = True) -> None:
    parsed = urlsplit(config.endpoint)
    if parsed.scheme != "https":
        raise ValueError("Remote MCP endpoints must use HTTPS")
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("MCP endpoint contains invalid authority or fragment")
    if parsed.query:
        raise ValueError("MCP endpoint query strings are not allowed")
    host = parsed.hostname.lower().rstrip(".")
    if config.allowed_hosts and host not in {item.lower().rstrip(".") for item in config.allowed_hosts}:
        raise ValueError("MCP endpoint host is not in the configured allowlist")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        if not address.is_global:
            raise ValueError("MCP endpoint must resolve to a public IP address")
        return
    if host in {"localhost", "localhost.localdomain"}:
        raise ValueError("Loopback MCP endpoints are not permitted")
    if resolve_dns:
        try:
            records = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError("MCP endpoint DNS resolution failed") from exc
        addresses = {address.split("%", 1)[0] for record in records if isinstance((address := record[4][0]), str)}
        if not addresses:
            raise ValueError("MCP endpoint has no DNS addresses")
        if any(not ipaddress.ip_address(value).is_global for value in addresses):
            raise ValueError("MCP endpoint resolves to a non-public address")


def _sse_messages(body: str) -> list[dict]:
    messages: list[dict] = []
    data: list[str] = []
    for line in body.splitlines():
        if not line:
            if data:
                messages.append(_decode_message("\n".join(data)))
                data = []
        elif line.startswith(":"):
            continue
        elif line.startswith("data:"):
            value = line[5:]
            data.append(value[1:] if value.startswith(" ") else value)
    if data:
        messages.append(_decode_message("\n".join(data)))
    return messages


def _decode_message(value: str) -> dict:
    try:
        result = json.loads(value)
    except json.JSONDecodeError as exc:
        raise McpProtocolError("MCP SSE event contained invalid JSON") from exc
    if not isinstance(result, dict):
        raise McpProtocolError("MCP SSE event must contain a JSON object")
    return result


class StreamableHttpTransport:
    """MCP Streamable HTTP POST transport with bounded, stateless responses."""

    def __init__(
        self,
        config: McpServerConfig,
        *,
        token_provider: Callable[[], str | None] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        validate_endpoint(config)
        self.config = config
        self._token_provider = token_provider
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(config.timeout_seconds),
            follow_redirects=False,
            trust_env=False,
        )
        self._owns_client = http_client is None
        self._lock = asyncio.Lock()
        self._request_id = 0

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _headers(self, *, initialize: bool = False) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if not initialize:
            headers["MCP-Protocol-Version"] = self.config.protocol_version
        token = self._token_provider() if self._token_provider else None
        if token:
            if "\r" in token or "\n" in token:
                raise ValueError("Bearer token contains invalid header characters")
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def notify(self, method: str, params: Mapping | None = None) -> None:
        if not self.config.enabled:
            raise McpTransportError("Remote MCP server is disabled")
        if not method.startswith("notifications/"):
            raise ValueError("MCP notification method must start with notifications/")
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = dict(params)
        try:
            async with self._client.stream(
                "POST", self.config.endpoint, headers=self._headers(), json=payload
            ) as response:
                body = await response.aread()
                if len(body) > 4096:
                    raise McpTransportError("MCP notification response exceeded size limit")
                if response.status_code not in {200, 202, 204} or body:
                    raise McpTransportError(
                        f"Remote MCP notification was not accepted (status={response.status_code}, body={bool(body)})"
                    )
        except httpx.TimeoutException as exc:
            raise McpTransportError("Remote MCP notification timed out") from exc
        except httpx.HTTPError as exc:
            raise McpTransportError("Remote MCP notification transport failed") from exc

    async def request(
        self,
        method: str,
        params: Mapping | None = None,
        *,
        initialize: bool = False,
    ) -> dict:
        if not self.config.enabled:
            raise McpTransportError("Remote MCP server is disabled")
        if not method or any(ord(ch) < 0x21 or ord(ch) > 0x7E for ch in method):
            raise ValueError("Invalid MCP method")
        async with self._lock:
            self._request_id += 1
            request_id = self._request_id
            payload = {
                "jsonrpc": "2.0", "id": request_id, "method": method,
                "params": dict(params or {}),
            }
            try:
                async with self._client.stream(
                    "POST", self.config.endpoint,
                    headers=self._headers(initialize=initialize), json=payload,
                ) as response:
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > self.config.max_response_bytes:
                            raise McpTransportError("MCP response exceeded configured size limit")
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                    if response.status_code >= 400:
                        raise McpTransportError(f"Remote MCP returned HTTP {response.status_code}")
                    if response.headers.get("MCP-Session-Id"):
                        raise McpTransportError(
                            "Remote MCP requires stateful sessions; this client is stateless"
                        )
                    media = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    if media == "application/json":
                        try:
                            messages = [json.loads(raw)]
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            raise McpProtocolError("Remote MCP returned invalid JSON") from exc
                    elif media == "text/event-stream":
                        try:
                            messages = _sse_messages(raw.decode("utf-8", errors="strict"))
                        except UnicodeDecodeError as exc:
                            raise McpProtocolError("Remote MCP SSE response was not UTF-8") from exc
                    else:
                        raise McpTransportError(f"Unsupported MCP content type: {media or 'missing'}")
            except httpx.TimeoutException as exc:
                raise McpTransportError("Remote MCP request timed out") from exc
            except httpx.HTTPError as exc:
                raise McpTransportError("Remote MCP HTTP transport failed") from exc
        for message in messages:
            if not isinstance(message, dict) or message.get("id") != request_id:
                continue
            if message.get("jsonrpc") != "2.0":
                raise McpProtocolError("Remote MCP response is not JSON-RPC 2.0")
            if "error" in message:
                error = message["error"]
                if not isinstance(error, dict):
                    raise McpProtocolError("Remote MCP returned malformed JSON-RPC error")
                raise McpProtocolError(
                    str(error.get("message", "Remote MCP error")),
                    code=error.get("code") if isinstance(error.get("code"), int) else None,
                    data=error.get("data"),
                )
            result = message.get("result")
            if not isinstance(result, dict):
                raise McpProtocolError("Remote MCP response has no result object")
            return result
        raise McpProtocolError("Remote MCP response did not contain the matching request ID")
