from __future__ import annotations

import asyncio
import os
from typing import Any
from urllib.parse import unquote

import httpx

from app.modules.agent_platform.application.tools.tool_handler import ToolHandler
from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.domain.tools.tool_result import ToolResult


class OpenListPathDenied(Exception):
    pass


def resolve_openlist_path(relative: str) -> str:
    root = os.getenv("OPENLIST_ROOT", "/waste-platform")

    if not isinstance(relative, str) or not relative:
        raise OpenListPathDenied()
    if len(relative) > 1024:
        raise OpenListPathDenied()
    if "\x00" in relative or "\\" in relative:
        raise OpenListPathDenied()
    if unquote(relative) != relative:
        raise OpenListPathDenied()
    if relative.startswith("/"):
        raise OpenListPathDenied()

    parts = [p for p in relative.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise OpenListPathDenied()

    path = root.rstrip("/")
    if parts:
        path += "/" + "/".join(parts)

    root = root.rstrip("/")
    if path != root and not path.startswith(root + "/"):
        raise OpenListPathDenied()

    return path


class OpenListMcpClient:
    _ALLOWED_TOOLS = {
        "openlist.fs.list",
        "openlist.fs.get",
    }

    def __init__(self) -> None:
        self._base_url = os.getenv(
            "OPENLIST_MCP_URL",
            "http://127.0.0.1:5244/mcp",
        ).rstrip("/")
        self._token = os.getenv("OPENLIST_MCP_TOKEN", "").strip()
        self._session_id: str | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()

    async def _rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any] | None:
        if not self._token:
            raise RuntimeError("OPENLIST_MCP_TOKEN missing")

        async with (
            self._lock,
            httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=2.0)) as client,
        ):
            self._request_id += 1

            headers = {
                "Authorization": self._token,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            if self._session_id:
                headers["Mcp-Session-Id"] = self._session_id

            payload = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params,
            }

            response = await client.post(
                self._base_url,
                headers=headers,
                json=payload,
            )

            if response.status_code in (401, 403):
                raise PermissionError("OpenList authentication failed")

            response.raise_for_status()

            session_id = response.headers.get("Mcp-Session-Id")
            if session_id:
                self._session_id = session_id

            # MCP notifications have no JSON-RPC response body.
            if method.startswith("notifications/"):
                return None

            data = response.json()

            if "error" in data:
                raise RuntimeError(str(data["error"].get("message", "MCP error")))

            return data["result"]

    async def initialize(self) -> None:
        if self._session_id:
            return

        await self._rpc(
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {
                    "name": "waste-platform",
                    "version": "1.0",
                },
            },
        )

        await self._rpc("notifications/initialized", {})

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        if tool_name not in self._ALLOWED_TOOLS:
            raise PermissionError("OpenList tool is not allowed")

        await self.initialize()

        result = await self._rpc(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )

        if not isinstance(result, dict):
            return result

        # Prefer MCP structuredContent. This is the canonical machine-readable
        # result and avoids exposing the transport envelope to Agent Platform.
        structured = result.get("structuredContent")
        if structured is not None:
            return structured

        # Fallback for MCP servers returning only content[].text.
        content = result.get("content")
        if isinstance(content, list):
            texts = [
                item.get("text")
                for item in content
                if isinstance(item, dict)
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
            ]

            if len(texts) == 1:
                import json

                try:
                    return json.loads(texts[0])
                except json.JSONDecodeError:
                    return texts[0]

            if texts:
                return texts

        return result


class OpenListListHandler(ToolHandler):
    _ALLOWED = frozenset({"path", "page", "per_page"})

    def __init__(self, client: OpenListMcpClient) -> None:
        self._client = client

    async def handle(self, request: ToolRequest) -> ToolResult:
        try:
            args = dict(request.arguments or {})
            unknown = set(args) - self._ALLOWED

            if unknown:
                return ToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    success=False,
                    error_code="invalid_arguments",
                    error_message="Nepodporované argumenty.",
                )

            path = resolve_openlist_path(args.get("path", ""))

            page = int(args.get("page", 1))
            per_page = int(args.get("per_page", 50))

            if page < 1 or per_page < 1 or per_page > 100:
                raise ValueError()

            data = await self._client.call_tool(
                "openlist.fs.list",
                {
                    "path": path,
                    "page": page,
                    "per_page": per_page,
                },
            )

            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=True,
                data=data,
            )

        except OpenListPathDenied:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="PATH_DENIED",
                error_message="Prístup k tejto ceste nie je povolený.",
            )
        except PermissionError:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="UPSTREAM_AUTH_FAILED",
                error_message="OpenList autorizácia zlyhala.",
            )
        except httpx.TimeoutException:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="UPSTREAM_TIMEOUT",
                error_message="OpenList neodpovedal včas.",
            )
        except Exception:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="UPSTREAM_UNAVAILABLE",
                error_message="OpenList nie je dostupný.",
            )


class OpenListGetHandler(ToolHandler):
    _ALLOWED = frozenset({"path"})

    def __init__(self, client: OpenListMcpClient) -> None:
        self._client = client

    async def handle(self, request: ToolRequest) -> ToolResult:
        try:
            args = dict(request.arguments or {})
            unknown = set(args) - self._ALLOWED

            if unknown:
                return ToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    success=False,
                    error_code="invalid_arguments",
                    error_message="Nepodporované argumenty.",
                )

            path = resolve_openlist_path(args.get("path", ""))

            data = await self._client.call_tool(
                "openlist.fs.get",
                {"path": path},
            )

            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=True,
                data=data,
            )

        except OpenListPathDenied:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="PATH_DENIED",
                error_message="Prístup k tejto ceste nie je povolený.",
            )
        except PermissionError:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="UPSTREAM_AUTH_FAILED",
                error_message="OpenList autorizácia zlyhala.",
            )
        except httpx.TimeoutException:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="UPSTREAM_TIMEOUT",
                error_message="OpenList neodpovedal včas.",
            )
        except Exception:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="UPSTREAM_UNAVAILABLE",
                error_message="OpenList nie je dostupný.",
            )
