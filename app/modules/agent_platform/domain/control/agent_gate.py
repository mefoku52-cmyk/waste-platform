"""Server-side gate that maps the platform ControlMode to what the chat agent
may do in a single turn.

This is the single source of truth and lives in the domain layer so it can be
unit-tested without a database. The chat endpoint resolves the current mode via
the control service and consults this gate *before* invoking the agent, so a
disabling mode stops both the generated text and every action (client action or
server tool call) the agent would otherwise trigger.

Semantics (mirrors the operators' control model -- see ``ControlMode``):

- ``NORMAL``      -> agent runs, actions allowed.
- ``READ_ONLY``   -> agent runs for reading, but mutating actions are suppressed.
- ``AI_DISABLED`` -> agent does not run (whole turn rejected).
- ``LOCKDOWN``    -> agent does not run (whole turn rejected).
- ``EMERGENCY``   -> agent does not run (whole turn rejected).

Note: today every server-side tool is read-only by design (see
``infrastructure/tools/tool_schemas.py``), so ``READ_ONLY`` only needs to
suppress mutating *client* actions. If a mutating server tool is ever added it
must be guarded here as well and blocked *before* it executes.
"""

from __future__ import annotations

from dataclasses import dataclass

from .control_mode import ControlMode

# Client actions that change stored state / enter data. Suppressed in READ_ONLY.
# Keep in sync with the mutating entries of ``CLIENT_ACTION_NAMES``.
MUTATING_CLIENT_ACTIONS: frozenset[str] = frozenset({"fill_form_field"})

# Modes in which the agent must not run at all (whole turn rejected).
_BLOCKED_MODES: frozenset[ControlMode] = frozenset(
    {
        ControlMode.AI_DISABLED,
        ControlMode.LOCKDOWN,
        ControlMode.EMERGENCY,
    }
)


@dataclass(frozen=True, slots=True)
class AgentGate:
    """Decision for one chat turn, derived from the platform ControlMode."""

    allowed: bool
    allow_mutations: bool
    mode: ControlMode

    def allows_client_action(self, name: str) -> bool:
        """Whether a client action may be surfaced to the frontend this turn."""
        if not self.allowed:
            return False
        return self.allow_mutations or name not in MUTATING_CLIENT_ACTIONS


def resolve_agent_gate(mode: ControlMode) -> AgentGate:
    """Map a ControlMode to the agent's permissions for the current turn."""
    if mode in _BLOCKED_MODES:
        return AgentGate(allowed=False, allow_mutations=False, mode=mode)
    if mode == ControlMode.READ_ONLY:
        return AgentGate(allowed=True, allow_mutations=False, mode=mode)
    return AgentGate(allowed=True, allow_mutations=True, mode=mode)
