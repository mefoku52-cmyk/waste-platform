"""Deny-by-default allowlist policy engine for agent tool execution.

The agent platform never authorizes itself.
This is the first concrete PolicyEngine: it allows only tool names that
are explicitly registered by the application boundary.
"""

from __future__ import annotations

from app.modules.agent_platform.application.policy.policy_engine import PolicyEngine
from app.modules.agent_platform.domain.policy.policy_context import PolicyContext
from app.modules.agent_platform.domain.policy.policy_decision import (
    PolicyDecision,
    PolicyOutcome,
)


class AllowlistPolicyEngine(PolicyEngine):
    """Allows only explicitly allowlisted tool names.

    Any tool not present in the allowlist is denied.
    Missing or empty tool name is denied.
    """

    def __init__(self, *, allowed_tool_names: frozenset[str]) -> None:
        self._allowed = frozenset(
            name.strip() for name in allowed_tool_names if name and name.strip()
        )

    async def decide(self, context: PolicyContext) -> PolicyDecision:
        tool_name = (context.tool_name or "").strip()
        if not tool_name:
            return PolicyDecision(
                outcome=PolicyOutcome.DENY,
                rule_id="policy.missing_tool_name",
                reason="Tool name is missing or empty.",
            )
        if tool_name not in self._allowed:
            return PolicyDecision(
                outcome=PolicyOutcome.DENY,
                rule_id="policy.unknown_tool",
                reason=f"Tool '{tool_name}' is not in the allowlist.",
            )
        return PolicyDecision(
            outcome=PolicyOutcome.ALLOW,
            rule_id="policy.allowlisted_tool",
            reason=f"Tool '{tool_name}' is allowlisted.",
        )
