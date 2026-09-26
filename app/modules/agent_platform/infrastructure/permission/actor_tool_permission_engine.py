"""Actor + tool scope permission engine.

The agent platform never authorizes itself.
This is the first concrete PermissionEngine: it allows only known actor
types to call tools whose (resource, action) pair is explicitly
allowlisted by the application boundary.

Missing actor, unknown actor type, or out-of-allowlist scope is denied.
"""

from __future__ import annotations

from app.modules.agent_platform.application.permission.permission_engine import (
    PermissionEngine,
)
from app.modules.agent_platform.domain.permission.permission_decision import (
    PermissionDecision,
    PermissionOutcome,
)
from app.modules.agent_platform.domain.permission.permission_request import (
    PermissionRequest,
)


class ActorToolPermissionEngine(PermissionEngine):
    """Deny-by-default permission for agent tool execution."""

    def __init__(
        self,
        *,
        allowed_actor_types: frozenset[str],
        allowed_scopes: frozenset[tuple[str, str]],
    ) -> None:
        self._allowed_actor_types = frozenset(
            t.strip() for t in allowed_actor_types if t and t.strip()
        )
        self._allowed_scopes = frozenset(
            (r.strip(), a.strip())
            for (r, a) in allowed_scopes
            if r and a and r.strip() and a.strip()
        )

    async def authorize(self, request: PermissionRequest) -> PermissionDecision:
        actor_id = (request.actor_id or "").strip()
        actor_type = (request.actor_type or "").strip()

        if not actor_id:
            return PermissionDecision(
                outcome=PermissionOutcome.DENIED,
                reason="actor_id is missing or empty.",
                policy_rule_id="permission.missing_actor_id",
            )

        if actor_type not in self._allowed_actor_types:
            return PermissionDecision(
                outcome=PermissionOutcome.DENIED,
                reason=f"actor_type '{actor_type}' is not allowed.",
                policy_rule_id="permission.unknown_actor_type",
            )

        scope_key = (
            (request.scope.resource or "").strip(),
            (request.scope.action or "").strip(),
        )
        if scope_key not in self._allowed_scopes:
            return PermissionDecision(
                outcome=PermissionOutcome.DENIED,
                reason=(f"scope ({scope_key[0]}, {scope_key[1]}) is not in the allowlist."),
                policy_rule_id="permission.scope_not_allowed",
            )

        return PermissionDecision(
            outcome=PermissionOutcome.ALLOWED,
            reason="Actor and scope are allowlisted.",
            policy_rule_id="permission.allowlisted",
        )
