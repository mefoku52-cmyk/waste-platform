"""Role agentov a ich opravnenia.

Definuje role agentov (OBSERVER, ANALYST, COORDINATOR, ADMIN) s
odpovedajúcimi oprávneniami. Default-deny: neznáma operácia je zamietnutá.
Integruje sa s existujúcou PermissionPolicy zo permissions.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .permissions import PermissionPolicy


class AgentRole(Enum):
    """Role agentov v systeme. Predvolene OBSERVER (iba citanie)."""

    OBSERVER = "observer"
    ANALYST = "analyst"
    COORDINATOR = "coordinator"
    ADMIN = "admin"


# Mapping role -> povolene operácie (nadobudnutie nad PermissionPolicy)
ROLE_OPERATIONS: dict[AgentRole, frozenset[str]] = {
    AgentRole.OBSERVER: frozenset(
        {
            "read",
            "inspect",
            "status",
            "plan",
            "check",
        }
    ),
    AgentRole.ANALYST: frozenset(
        {
            "read",
            "inspect",
            "status",
            "plan",
            "check",
            "diagnose",
            "audit",
            "compare",
            "analyze",
        }
    ),
    AgentRole.COORDINATOR: frozenset(
        {
            "read",
            "inspect",
            "status",
            "plan",
            "check",
            "diagnose",
            "audit",
            "compare",
            "analyze",
            "coordinate",
            "approve",
            "retry",
        }
    ),
    AgentRole.ADMIN: frozenset(
        {
            "read",
            "inspect",
            "status",
            "plan",
            "check",
            "diagnose",
            "audit",
            "compare",
            "analyze",
            "coordinate",
            "approve",
            "retry",
            "configure",
            "override",
        }
    ),
}

# Operácie, ktoré sú vždy zakázané bez ohľadu na rolu
FORBIDDEN_FOR_ALL_ROLES: frozenset[str] = frozenset(
    {
        "write",
        "commit",
        "checkout",
        "reset",
        "migrate",
        "deploy",
        "install",
        "delete",
        "modify",
        "execute_shell",
        "create_db",
        "create_user",
        "drop_table",
        "truncate",
    }
)


@dataclass(frozen=True)
class Agent:
    """Agent s rolou a oprávneniami. Nemenný pre bezpečnosť."""

    name: str
    role: AgentRole = AgentRole.OBSERVER
    metadata: dict[str, Any] = field(default_factory=dict)

    def allowed_operations(self) -> frozenset[str]:
        """Vrati operácie povolené pre túto rolu."""
        return ROLE_OPERATIONS.get(self.role, frozenset())

    def is_allowed(self, operation: str) -> bool:
        """Ci je operácia povolená pre tohto agenta (default-deny)."""
        if operation in FORBIDDEN_FOR_ALL_ROLES:
            return False
        return operation in self.allowed_operations()


@dataclass(frozen=True)
class AgentPermission:
    """Vysledok kontroly oprávnenia agenta."""

    agent: str
    role: str
    operation: str
    allowed: bool
    reason: str


class AgentRoleManager:
    """Spravuje role agentov a ich oprávnenia."""

    def __init__(self, policy: PermissionPolicy | None = None):
        self.policy = policy or PermissionPolicy()
        self._agents: dict[str, Agent] = {}

    def register_agent(self, agent: Agent) -> None:
        """Registruje agenta."""
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Agent | None:
        """Vrati agenta podľa mena alebo None."""
        return self._agents.get(name)

    def check_agent(self, agent_name: str, operation: str) -> AgentPermission:
        """Skontroluje, ci agent smie vykonat operaciu.

        Pouziva double-check: najprv role-based povolenie, potom
        PermissionPolicy. PermissionPolicy blokuje iba explicitne zakazane
        operacie (FORBIDDEN_OPERATIONS); agentove role rozhoduju o vsetkych
        ostatnych. Default-deny pre zakazane a neznate operacie.
        """
        agent = self._agents.get(agent_name)
        if agent is None:
            return AgentPermission(
                agent=agent_name,
                role="unknown",
                operation=operation,
                allowed=False,
                reason=f"Agent '{agent_name}' nie je registrovaný",
            )

        # 1. Vzdy zakazane operacie
        if operation in FORBIDDEN_FOR_ALL_ROLES:
            return AgentPermission(
                agent=agent_name,
                role=agent.role.value,
                operation=operation,
                allowed=False,
                reason=f"Operacia '{operation}' je zakazana pre vsetky role",
            )

        # 2. Role-based kontrola
        role_allowed = agent.is_allowed(operation)
        if not role_allowed:
            return AgentPermission(
                agent=agent_name,
                role=agent.role.value,
                operation=operation,
                allowed=False,
                reason=f"Operacia '{operation}' nie je povolena pre rolu {agent.role.value}",
            )

        # 3. PermissionPolicy kontrola (double-check: rola aj politika musia povolit)
        policy_allowed = self.policy.is_allowed(operation)
        if not policy_allowed:
            return AgentPermission(
                agent=agent_name,
                role=agent.role.value,
                operation=operation,
                allowed=False,
                reason=f"Operacia '{operation}' je zakazana politikou {self.policy.mode.value}",
            )

        return AgentPermission(
            agent=agent_name,
            role=agent.role.value,
            operation=operation,
            allowed=True,
            reason="Povoleno",
        )

    def list_agents(self) -> list[str]:
        """Vrati zoznam registrovaných agentov."""
        return sorted(self._agents.keys())
