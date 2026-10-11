"""Agent orchestration – real implementation with tool calling loop."""

from __future__ import annotations

import contextlib
import json
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.modules.agent_platform.application.permission.permission_engine import (
    PermissionEngine,
)
from app.modules.agent_platform.application.policy.policy_engine import PolicyEngine
from app.modules.agent_platform.domain.events.event_source import EventSource
from app.modules.agent_platform.domain.events.event_type import PlatformEventType
from app.modules.agent_platform.domain.events.platform_event import PlatformEvent
from app.modules.agent_platform.domain.permission.permission_decision import (
    PermissionOutcome,
)
from app.modules.agent_platform.domain.permission.permission_request import (
    PermissionRequest,
)
from app.modules.agent_platform.domain.permission.permission_scope import (
    PermissionScope,
)
from app.modules.agent_platform.domain.policy.policy_context import PolicyContext
from app.modules.agent_platform.domain.policy.policy_decision import PolicyOutcome
from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse
from app.modules.agent_platform.infrastructure.events.event_publisher import (
    EventPublisher,
)
from app.modules.agent_platform.infrastructure.tools.client_action_validation import (
    ClientActionValidation,
    validate_client_action,
)

MAX_TOOL_ITERATIONS = 6


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    text: str
    tool_calls: tuple[dict[str, Any], ...]
    iterations: int
    provider: str | None = None


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
        policy: PolicyEngine | None = None,
        permission: PermissionEngine | None = None,
        tool_scopes: dict[str, tuple[str, str]] | None = None,
        audit: Callable[[str, str, str, float], Awaitable[None]] | None = None,
        event_publisher: EventPublisher | None = None,
        client_tool_names: frozenset[str] | None = None,
        client_action_validator: (
            Callable[[str, Mapping[str, Any]], ClientActionValidation] | None
        ) = None,
    ) -> None:
        self._gateway = gateway
        self._tool_schemas = tuple(tool_schemas)
        self._tool_handlers = dict(tool_handlers)
        self._model = model
        self._policy = policy
        self._permission = permission
        self._tool_scopes = dict(tool_scopes or {})
        self._audit = audit
        self._event_publisher = event_publisher
        self._client_tool_names: frozenset[str] = frozenset(client_tool_names or ())
        # Secure by default: validation is always applied to client actions.
        self._client_action_validator: Callable[
            [str, Mapping[str, Any]], ClientActionValidation
        ] = client_action_validator or validate_client_action

    async def _safe_audit(
        self,
        actor_id: str,
        tool_name: str,
        outcome: str,
        duration_s: float,
    ) -> None:
        """Best-effort audit. Failure must never break the tool call."""
        if self._audit is None:
            return
        with contextlib.suppress(Exception):
            await self._audit(actor_id, tool_name, outcome, duration_s)

    async def _safe_publish(
        self,
        actor_id: str,
        tool_name: str,
        event_type: PlatformEventType,
        source: EventSource,
    ) -> None:
        """Best-effort event publish. Failure must never break the tool call."""
        publisher = self._event_publisher
        if publisher is None:
            return
        with contextlib.suppress(Exception):
            event = PlatformEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                source=source,
                occurred_at=datetime.now(UTC),
                actor_id=actor_id,
                target=tool_name,
                payload={"tool_name": tool_name},
            )
            await publisher.publish(event)

    async def respond(
        self,
        *,
        system_prompt: str,
        user_message: str,
        actor_id: str,
        actor_type: str = "user",
        session_id: str | None = None,
        conversation_history: tuple[ModelMessage, ...] | None = None,
    ) -> OrchestrationResult:
        session_id = session_id or str(uuid.uuid4())
        messages: list[ModelMessage] = [
            ModelMessage(role="system", content=system_prompt),
        ]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append(ModelMessage(role="user", content=user_message))

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
                    provider=response.provider_metadata.get("provider"),
                )

            messages.append(
                ModelMessage(
                    role="assistant",
                    content=response.text or None,
                    tool_calls=response.tool_calls,
                )
            )

            for call in response.tool_calls:
                t0 = time.monotonic()
                tool_name = ""
                outcome = "not_started"
                _fn_pre = call.get("function", {}) or {}
                _tool_pre = _fn_pre.get("name", "")
                if _tool_pre:
                    await self._safe_publish(
                        actor_id,
                        _tool_pre,
                        PlatformEventType.TOOL_REQUESTED,
                        EventSource.AI,
                    )
                try:
                    fn = call.get("function", {}) or {}
                    tool_name = fn.get("name", "")
                    raw_args = fn.get("arguments", "{}")
                    try:
                        args = (
                            json.loads(raw_args)
                            if isinstance(raw_args, str)
                            else dict(raw_args or {})
                        )
                    except (TypeError, ValueError):
                        args = {}

                    # Client actions are appended only after policy + permission
                    # pass and their arguments are validated, so a denied or
                    # malformed action is never handed to the frontend.
                    is_client_action = tool_name in self._client_tool_names
                    if not is_client_action:
                        collected_calls.append(
                            {"name": tool_name, "arguments": args, "id": call.get("id", "")}
                        )

                    if self._policy is not None:
                        decision = await self._policy.decide(
                            PolicyContext(
                                actor_id=actor_id,
                                actor_type=actor_type,
                                agent_id=None,
                                action="tool.call",
                                target=None,
                                tool_name=tool_name,
                                risk_level=None,
                                attributes={},
                            )
                        )
                        if decision.outcome == PolicyOutcome.DENY:
                            outcome = "denied_by_policy"
                            messages.append(
                                ModelMessage(
                                    role="tool",
                                    content=json.dumps(
                                        {
                                            "error": "tool_denied_by_policy",
                                            "tool_name": tool_name,
                                            "rule_id": decision.rule_id,
                                            "reason": decision.reason,
                                        },
                                        ensure_ascii=False,
                                    ),
                                    tool_call_id=call.get("id", ""),
                                )
                            )
                            continue
                        if decision.outcome == PolicyOutcome.REQUIRE_APPROVAL:
                            outcome = "requires_approval_policy"
                            messages.append(
                                ModelMessage(
                                    role="tool",
                                    content=json.dumps(
                                        {
                                            "error": "tool_requires_approval",
                                            "tool_name": tool_name,
                                            "rule_id": decision.rule_id,
                                            "reason": decision.reason,
                                        },
                                        ensure_ascii=False,
                                    ),
                                    tool_call_id=call.get("id", ""),
                                )
                            )
                            continue

                    if self._permission is not None:
                        scope_pair = self._tool_scopes.get(tool_name)
                        if scope_pair is None:
                            outcome = "tool_scope_unmapped"
                            messages.append(
                                ModelMessage(
                                    role="tool",
                                    content=json.dumps(
                                        {
                                            "error": "tool_scope_unmapped",
                                            "tool_name": tool_name,
                                        },
                                        ensure_ascii=False,
                                    ),
                                    tool_call_id=call.get("id", ""),
                                )
                            )
                            continue
                        perm_decision = await self._permission.authorize(
                            PermissionRequest(
                                request_id=str(uuid.uuid4()),
                                actor_id=actor_id,
                                actor_type=actor_type,
                                scope=PermissionScope(
                                    resource=scope_pair[0],
                                    action=scope_pair[1],
                                ),
                                reason="agent_tool_call",
                            )
                        )
                        if perm_decision.outcome == PermissionOutcome.DENIED:
                            outcome = "denied_by_permission"
                            messages.append(
                                ModelMessage(
                                    role="tool",
                                    content=json.dumps(
                                        {
                                            "error": "tool_denied_by_permission",
                                            "tool_name": tool_name,
                                            "rule_id": perm_decision.policy_rule_id,
                                            "reason": perm_decision.reason,
                                        },
                                        ensure_ascii=False,
                                    ),
                                    tool_call_id=call.get("id", ""),
                                )
                            )
                            continue
                        if perm_decision.outcome == PermissionOutcome.APPROVAL_REQUIRED:
                            outcome = "requires_approval_permission"
                            messages.append(
                                ModelMessage(
                                    role="tool",
                                    content=json.dumps(
                                        {
                                            "error": "tool_requires_permission_approval",
                                            "tool_name": tool_name,
                                            "rule_id": perm_decision.policy_rule_id,
                                            "reason": perm_decision.reason,
                                        },
                                        ensure_ascii=False,
                                    ),
                                    tool_call_id=call.get("id", ""),
                                )
                            )
                            continue

                    # Client-side action: nevykonávame handler, iba validujeme
                    # argumenty a potvrdíme modelu že frontend to vykoná.
                    if is_client_action:
                        validation = self._client_action_validator(tool_name, args)
                        if not validation.valid:
                            outcome = "client_action_invalid_arguments"
                            messages.append(
                                ModelMessage(
                                    role="tool",
                                    content=json.dumps(
                                        {
                                            "error": "client_action_invalid_arguments",
                                            "tool_name": tool_name,
                                            "error_code": validation.error_code,
                                            "reason": validation.error_message,
                                        },
                                        ensure_ascii=False,
                                    ),
                                    tool_call_id=call.get("id", ""),
                                )
                            )
                            continue
                        collected_calls.append(
                            {
                                "name": tool_name,
                                "arguments": dict(validation.arguments),
                                "id": call.get("id", ""),
                            }
                        )
                        outcome = "dispatched_to_client"
                        messages.append(
                            ModelMessage(
                                role="tool",
                                content=json.dumps(
                                    {
                                        "success": True,
                                        "client_action": True,
                                        "note": (
                                            "Client action dispatched to frontend. "
                                            "It will be executed on the current page. "
                                            "You may now summarize or ask a follow-up."
                                        ),
                                    },
                                    ensure_ascii=False,
                                ),
                                tool_call_id=call.get("id", ""),
                            )
                        )
                        continue

                    handler = self._tool_handlers.get(tool_name)
                    if handler is None:
                        outcome = "tool_not_available"
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
                        outcome = "executed" if result.success else "failed"
                        payload = {
                            "success": result.success,
                            "data": result.data,
                            "error_code": result.error_code,
                            "error_message": result.error_message,
                        }
                    except Exception as exc:
                        outcome = "exception"
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
                finally:
                    await self._safe_audit(
                        actor_id,
                        tool_name,
                        outcome,
                        time.monotonic() - t0,
                    )
                    _completed_type = _outcome_to_event_type(outcome)
                    await self._safe_publish(
                        actor_id,
                        tool_name,
                        _completed_type,
                        EventSource.TOOL,
                    )

        return OrchestrationResult(
            text="Prepáč, nepodarilo sa mi dokončiť odpoveď v rozumnom čase.",
            tool_calls=tuple(collected_calls),
            iterations=MAX_TOOL_ITERATIONS,
        )


def _outcome_to_event_type(outcome: str) -> PlatformEventType:
    if outcome in {"executed", "dispatched_to_client"}:
        return PlatformEventType.TOOL_EXECUTED
    if outcome in {"failed", "exception"}:
        return PlatformEventType.TOOL_FAILED
    if outcome in {
        "denied_by_policy",
        "denied_by_permission",
        "tool_scope_unmapped",
        "tool_not_available",
        "client_action_invalid_arguments",
    }:
        return PlatformEventType.TOOL_DENIED
    if outcome in {"requires_approval_policy", "requires_approval_permission"}:
        return PlatformEventType.APPROVAL_REQUESTED
    return PlatformEventType.TOOL_FAILED
