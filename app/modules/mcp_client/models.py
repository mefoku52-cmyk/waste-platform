"""Validated configuration for remote MCP servers."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class McpServerConfig:
    endpoint: str
    enabled: bool = True
    allowed_hosts: tuple[str, ...] | list[str] = ()
    timeout_seconds: float = 30.0
    protocol_version: str = "2025-11-25"
    max_response_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        if not isinstance(self.endpoint, str) or not self.endpoint.strip():
            raise ValueError("MCP endpoint is required")

        if not isinstance(self.enabled, bool):
            raise ValueError("MCP enabled must be boolean")

        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or not 0 < self.timeout_seconds <= 300
        ):
            raise ValueError("MCP timeout must be between 0 and 300 seconds")

        if (
            isinstance(self.max_response_bytes, bool)
            or not isinstance(self.max_response_bytes, int)
            or not 1 <= self.max_response_bytes <= 16 * 1024 * 1024
        ):
            raise ValueError("MCP max_response_bytes must be between 1 and 16777216")

        if not isinstance(self.protocol_version, str):
            raise ValueError("Invalid MCP protocol version")

        version = self.protocol_version.strip()
        if not version or any(ord(ch) < 0x21 or ord(ch) > 0x7E for ch in version):
            raise ValueError("Invalid MCP protocol version")

        if isinstance(self.allowed_hosts, str):
            raise ValueError("allowed_hosts must be a sequence of hostnames")

        normalized: list[str] = []

        for raw_host in self.allowed_hosts:
            if not isinstance(raw_host, str):
                raise ValueError("Invalid MCP allowlist entry")

            host = raw_host.strip().rstrip(".")

            if not host or host == "*":
                raise ValueError("Wildcard or empty MCP allowlist entry is forbidden")

            try:
                host = host.encode("idna").decode("ascii").lower()
            except UnicodeError as exc:
                raise ValueError("Invalid MCP allowlist hostname") from exc

            normalized.append(host)

        object.__setattr__(self, "allowed_hosts", tuple(dict.fromkeys(normalized)))
        object.__setattr__(self, "protocol_version", version)
