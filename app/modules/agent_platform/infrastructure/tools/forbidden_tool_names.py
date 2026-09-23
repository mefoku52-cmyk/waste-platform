"""Forbidden capability names.

The Agent Platform must never expose these as ordinary AI tools.
"""

FORBIDDEN_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "shell.execute",
        "terminal.execute",
        "bash.execute",
        "sh.execute",
        "python.execute",
        "filesystem.read",
        "filesystem.write",
        "filesystem.delete",
        "filesystem.execute",
        "sql.execute",
        "database.sql",
        "database.raw_query",
        "database.credentials",
        "secrets.read",
        "environment.read",
        "credentials.read",
        "jwt.sign",
        "jwt.issue",
        "admin.grant",
        "admin.revoke",
        "permission.grant",
        "permission.escalate",
        "security.disable",
        "audit.delete",
    }
)


def is_forbidden_tool_name(name: str) -> bool:
    return name.strip().lower() in FORBIDDEN_TOOL_NAMES
