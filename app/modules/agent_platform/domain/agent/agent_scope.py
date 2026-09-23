"""Agent scope."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AgentScope:
    """Logical scope available to an agent session.

    Scope describes where the agent operates. It does not itself authorize
    an operation.
    """

    user_id: str | None = None
    company_id: str | None = None
    admin_scope: str | None = None
    allowed_domains: frozenset[str] = field(default_factory=frozenset)

    def contains_domain(self, domain: str) -> bool:
        return domain in self.allowed_domains
