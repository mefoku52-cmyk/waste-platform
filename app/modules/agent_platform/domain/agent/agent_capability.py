"""Agent capability definitions."""

from enum import Enum


class AgentCapability(str, Enum):
    """Capabilities an agent may request.

    A capability is not an authorization grant.
    The policy and permission layers still decide whether it is usable.
    """

    READ = "read"
    SEARCH = "search"
    PREPARE = "prepare"
    ACT = "act"
