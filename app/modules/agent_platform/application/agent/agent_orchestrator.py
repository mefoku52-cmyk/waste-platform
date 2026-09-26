"""Agent orchestration – real implementation with tool calling loop."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

MAX_TOOL_ITERATIONS = 4


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    text: str
    tool_calls: tuple[dict[str, Any], ...]
    iterations: int


class AgentOrchestrator:
    """Coordinates model reasoning and tool execution.

    The orchestrator never authorizes itself – authorization happens in the
    tool handlers, which are wired with the caller's scope.
    """

    def __init__(
        self,
        *,
        gateway: ModelGateway,
        tool_schemas: tuple[dict[str, Any], ...],
        tool_handlers: dict[str, Any],
        model: str,
    ) -> None:
        self._gateway = gateway
        self._tool_schemas = tuple(tool_schemas)
        self._tool_handlers = dict(tool_handlers)
        self._model = model

    async def respond(
        self,
        *,
        system_prompt: str,
        user_message: str,
        actor_id: str,
        actor_type: str = "user",
        session_id: str | None = None,
    ) -> OrchestrationResult:
        session_id = session_id or str(uuid.uuid4())
        messages: list[ModelMessage] = [
            ModelMessage(role="system", content=system_prompt),
            ModelMessage(role="user", content=user_message),
        ]

        collected_calls: list[dict[str, Any]] = []

        for iteration in range(MAX_TOOL_ITERATIONS):
            response: ModelResponse = await self._gateway.generate(
                ModelRequest(
                    request_id=str(uuid.uuid4()),
                    model=self._model,
                    messages=tuple(messages),
                    temperature=0.2,
                    tools=self._tool_schemas,
                    tool_choice="auto",
                )
            )

            if not response.tool_calls:
                return OrchestrationResult(
                    text=response.text.strip(),
                    tool_calls=tuple(collected_calls),
                    iterations=iteration + 1,
                )

            messages.append(
                ModelMessage(
                    role="assistant",
                    content=response.text or None,
                    tool_calls=response.tool_calls,
                )
            )

            for call in response.tool_calls:
                fn = call.get("function", {}) or {}
                tool_name = fn.get("name", "")
                raw_args = fn.get("arguments", "{}")
                try:
                    args = (
                        json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args or {})
                    )
                except (TypeError, ValueError):
                    args = {}

                collected_calls.append(
                    {"name": tool_name, "arguments": args, "id": call.get("id", "")}
                )

                handler = self._tool_handlers.get(tool_name)
                if handler is None:
                    messages.append(
                        ModelMessage(
                            role="tool",
                            content=json.dumps(
                                {"error": "tool_not_available", "name": tool_name},
                                ensure_ascii=False,
                            ),
                            tool_call_id=call.get("id", ""),
                        )
                    )
                    continue

                try:
                    result = await handler.handle(
                        ToolRequest(
                            request_id=str(uuid.uuid4()),
                            tool_name=tool_name,
                            actor_id=actor_id,
                            actor_type=actor_type,
                            arguments=args,
                            reason="agent_tool_call",
                        )
                    )
                    payload = {
                        "success": result.success,
                        "data": result.data,
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                    }
                except Exception as exc:
                    payload = {
                        "success": False,
                        "error_code": "tool_exception",
                        "error_message": type(exc).__name__,
                    }

                messages.append(
                    ModelMessage(
                        role="tool",
                        content=json.dumps(payload, ensure_ascii=False, default=str),
                        tool_call_id=call.get("id", ""),
                    )
                )

        return OrchestrationResult(
            text="Prepáč, nepodarilo sa mi dokončiť odpoveď v rozumnom čase.",
            tool_calls=tuple(collected_calls),
            iterations=MAX_TOOL_ITERATIONS,
        )
