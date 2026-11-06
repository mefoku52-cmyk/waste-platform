"""Typed exceptions for the remote MCP client."""

from __future__ import annotations


class McpError(Exception):
    """Base exception for MCP client failures."""


class McpTransportError(McpError):
    """HTTP or transport-level MCP failure."""


class McpProtocolError(McpError):
    """Invalid JSON-RPC or MCP protocol response."""

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        data: object | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.data = data
