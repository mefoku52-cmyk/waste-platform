from __future__ import annotations

import asyncio
import ipaddress
import json
import socket
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlsplit

import httpx

from .errors import McpProtocolError, McpTransportError
from .models import McpServerConfig


def validate_endpoint(
    config: McpServerConfig,
    *,
    resolve_dns: bool = True,
) -> None:
    try:
        parsed = urlsplit(config.endpoint)
        port = parsed.port if parsed.port is not None else 443
    except ValueError as exc:
        raise ValueError("MCP endpoint URL is malformed") from exc

    if parsed.scheme != "https":
        raise ValueError("Remote MCP endpoints must use HTTPS")

    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("MCP endpoint contains invalid authority or fragment")

    if parsed.query:
        raise ValueError("MCP endpoint query strings are not allowed")

    if not 1 <= port <= 65535:
        raise ValueError("MCP endpoint port is invalid")

    host = parsed.hostname.lower().rstrip(".")

    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("MCP endpoint hostname is invalid") from exc

    if config.allowed_hosts and host not in config.allowed_hosts:
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

    if not resolve_dns:
        return

    try:
        records = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM,
        )
    except OSError as exc:
        raise ValueError("MCP endpoint DNS resolution failed") from exc

    addresses: set[str] = set()

    for record in records:
        raw_address = record[4][0]

        if not isinstance(raw_address, str):
            continue

        value = raw_address.split("%", 1)[0]

        try:
            parsed_address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise ValueError("MCP endpoint DNS returned an invalid address") from exc

        if not parsed_address.is_global:
            raise ValueError("MCP endpoint resolves to a non-public address")

        addresses.add(value)

    if not addresses:
        raise ValueError("MCP endpoint has no DNS addresses")


def _decode_message(value: str) -> dict[str, Any]:
    try:
        result = json.loads(value)
    except json.JSONDecodeError as exc:
        raise McpProtocolError("MCP SSE event contained invalid JSON") from exc

    if not isinstance(result, dict):
        raise McpProtocolError("MCP SSE event must contain a JSON object")

    return result


def _sse_messages(body: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
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


class StreamableHttpTransport:
    """MCP Streamable HTTP POST transport with bounded responses."""

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

    async def notify(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
    ) -> None:
        if not self.config.enabled:
            raise McpTransportError("Remote MCP server is disabled")

        if not method.startswith("notifications/"):
            raise ValueError("MCP notification method must start with notifications/")

        validate_endpoint(self.config)

        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }

        if params is not None:
            payload["params"] = dict(params)

        limit = min(4096, self.config.max_response_bytes)

        try:
            async with self._client.stream(
                "POST",
                self.config.endpoint,
                headers=self._headers(),
                json=payload,
                follow_redirects=False,
            ) as response:
                if response.status_code not in {200, 202, 204}:
                    raise McpTransportError("Remote MCP notification was not accepted")

                total = 0

                async for chunk in response.aiter_bytes():
                    total += len(chunk)

                    if total > limit:
                        raise McpTransportError("MCP notification response exceeded size limit")

                    if total:
                        raise McpTransportError("MCP notification response must not contain a body")

        except httpx.TimeoutException as exc:
            raise McpTransportError("Remote MCP notification timed out") from exc
        except httpx.HTTPError as exc:
            raise McpTransportError("Remote MCP notification transport failed") from exc

    async def request(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
        *,
        initialize: bool = False,
    ) -> dict[str, Any]:
        if not self.config.enabled:
            raise McpTransportError("Remote MCP server is disabled")

        if not method or any(ord(ch) < 0x21 or ord(ch) > 0x7E for ch in method):
            raise ValueError("Invalid MCP method")

        validate_endpoint(self.config)

        async with self._lock:
            self._request_id += 1
            request_id = self._request_id

            payload: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": dict(params or {}),
            }

            try:
                async with self._client.stream(
                    "POST",
                    self.config.endpoint,
                    headers=self._headers(initialize=initialize),
                    json=payload,
                    follow_redirects=False,
                ) as response:
                    if response.status_code != 200:
                        raise McpTransportError(f"Remote MCP returned HTTP {response.status_code}")

                    if response.headers.get("MCP-Session-Id"):
                        raise McpTransportError(
                            "Remote MCP requires stateful sessions; this client is stateless"
                        )

                    limit = self.config.max_response_bytes
                    content_length = response.headers.get("content-length")

                    if content_length is not None:
                        try:
                            declared_size = int(content_length)
                        except ValueError as exc:
                            raise McpProtocolError(
                                "Remote MCP returned invalid Content-Length"
                            ) from exc

                        if declared_size < 0 or declared_size > limit:
                            raise McpTransportError("MCP response exceeded configured size limit")

                    chunks: list[bytes] = []
                    total = 0

                    async for chunk in response.aiter_bytes():
                        total += len(chunk)

                        if total > limit:
                            raise McpTransportError("MCP response exceeded configured size limit")

                        chunks.append(chunk)

                    raw = b"".join(chunks)

                    media = (
                        response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    )

                    if media == "application/json":
                        try:
                            decoded = json.loads(raw)
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            raise McpProtocolError("Remote MCP returned invalid JSON") from exc

                        if not isinstance(decoded, dict):
                            raise McpProtocolError("Remote MCP JSON response must be an object")

                        messages = [decoded]

                    elif media == "text/event-stream":
                        try:
                            body = raw.decode("utf-8", errors="strict")
                        except UnicodeDecodeError as exc:
                            raise McpProtocolError("Remote MCP SSE response was not UTF-8") from exc

                        messages = _sse_messages(body)

                    else:
                        raise McpTransportError(
                            f"Unsupported MCP content type: {media or 'missing'}"
                        )

            except httpx.TimeoutException as exc:
                raise McpTransportError("Remote MCP request timed out") from exc
            except httpx.HTTPError as exc:
                raise McpTransportError("Remote MCP HTTP transport failed") from exc

        for message in messages:
            if message.get("id") != request_id:
                continue

            if message.get("jsonrpc") != "2.0":
                raise McpProtocolError("Remote MCP response is not JSON-RPC 2.0")

            if "error" in message:
                error = message["error"]

                if not isinstance(error, dict):
                    raise McpProtocolError("Remote MCP returned malformed JSON-RPC error")

                code = error.get("code")

                raise McpProtocolError(
                    str(error.get("message", "Remote MCP error")),
                    code=(code if isinstance(code, int) and not isinstance(code, bool) else None),
                    data=error.get("data"),
                )

            result = message.get("result")

            if not isinstance(result, dict):
                raise McpProtocolError("Remote MCP response has no result object")

            return result

        raise McpProtocolError("Remote MCP response did not contain the matching request ID")
