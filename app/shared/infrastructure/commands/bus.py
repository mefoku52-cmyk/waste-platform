"""Idempotent command bus for business operations."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    success: bool
    data: Any = None
    error: str | None = None
    idempotency_key: str | None = None


class CommandBus:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._processed: dict[str, CommandResult] = {}  # in-memory; replace with DB in full impl

    def register(self, command_name: str, handler: Callable[..., Awaitable[Any]]) -> None:
        self._handlers[command_name] = handler

    async def execute(self, command_name: str, payload: dict[str, Any], idempotency_key: str | None = None) -> CommandResult:
        key = idempotency_key or self._derive_key(command_name, payload)
        if key in self._processed:
            logger.info("idempotent hit for %s", key)
            return self._processed[key]

        handler = self._handlers.get(command_name)
        if not handler:
            return CommandResult(success=False, error=f"No handler for {command_name}")

        try:
            result = await handler(payload)
            cmd_result = CommandResult(success=True, data=result, idempotency_key=key)
        except Exception as exc:
            cmd_result = CommandResult(success=False, error=str(exc), idempotency_key=key)

        self._processed[key] = cmd_result
        return cmd_result

    def _derive_key(self, name: str, payload: dict[str, Any]) -> str:
        raw = f"{name}:{sorted(payload.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]


# Global instance for registration
command_bus = CommandBus()