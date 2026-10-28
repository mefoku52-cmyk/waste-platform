"""Politika opravneni - režim iba na citanie. Default-deny pre vsetky režimy."""

from __future__ import annotations

from enum import Enum


class PermissionMode(Enum):
    READ_ONLY = "read_only"
    DIAGNOSTIC = "diagnostic"


class PermissionPolicy:
    """Opravnenia systemu. Predvolene iba citanie. Neznama operacia = zamietnuta."""

    FORBIDDEN_OPERATIONS = frozenset(
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

    ALLOWED_OPERATIONS: dict[PermissionMode, frozenset[str]] = {
        PermissionMode.READ_ONLY: frozenset(
            {
                "read",
                "inspect",
                "status",
                "plan",
                "check",
            }
        ),
        PermissionMode.DIAGNOSTIC: frozenset(
            {
                "read",
                "inspect",
                "status",
                "plan",
                "check",
                "diagnose",
                "audit",
                "analyze",
                "compare",
                "coordinate",
            }
        ),
    }

    def __init__(self, mode: PermissionMode = PermissionMode.READ_ONLY):
        self.mode = mode

    def is_allowed(self, operation: str) -> bool:
        if operation in self.FORBIDDEN_OPERATIONS:
            return False
        allowed = self.ALLOWED_OPERATIONS.get(self.mode, frozenset())
        return operation in allowed

    def check(self, operation: str) -> None:
        if not self.is_allowed(operation):
            raise PermissionError(f"Operacia '{operation}' je zakazana v rezime {self.mode.value}")
