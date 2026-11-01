"""Git diagnostika - IBA CITANIE stavu repozitara. Nikdy nemeni pracovny strom."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class GitDiagnostic:
    """Iba citanie git stavu. Ziadne mutujuce operacie. Vynucuje read-only."""

    READ_ONLY_COMMANDS = frozenset(
        {
            "status",
            "log",
            "diff",
            "branch",
            "rev-parse",
            "show",
            "ls-files",
            "cat-file",
            "describe",
            "rev-list",
        }
    )

    # Povolene argumenty pre kazdy prikaz
    _ALLOWED_ARGS = {
        "status": {r"^--porcelain(?:=v1)?$"},
        "log": {r"^-([1-9]|[1-9][0-9])$", r"^--oneline$"},
        "diff": set(),
        "branch": {r"^--show-current$"},
        "rev-parse": {r"^--is-inside-work-tree$"},
        "show": set(),
        "ls-files": set(),
    }

    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Cesta neexistuje: {self.repo_path}")
        git_dir = self.repo_path / ".git"
        if not (git_dir.exists() or git_dir.is_file()):
            raise ValueError(f"Nie je Git repozitar: {self.repo_path}")
        if shutil.which("git") is None:
            raise RuntimeError("git binary nie je dostupny")

    def _validate_args(self, args: list[str]) -> None:
        cmd = args[0]
        allowed = self._ALLOWED_ARGS.get(cmd, set())
        for arg in args[1:]:
            if not any(re.fullmatch(p, arg) for p in allowed):
                raise PermissionError(f"Nepovoleny argument: {arg}")

    def _run(self, args: list[str]) -> tuple[int, str, str]:
        """Spusti git prikaz. Iba read-only. Vrati (returncode, stdout, stderr)."""
        if not args or args[0] not in self.READ_ONLY_COMMANDS:
            raise PermissionError(f"Git prikaz nie je povoleny (read-only): {args}")
        self._validate_args(args)
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path)] + args,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout, result.stderr
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return -1, "", str(e)

    def status(self) -> dict[str, Any]:
        rc, out, err = self._run(["status", "--porcelain"])
        return {
            "returncode": rc,
            "changes": out.strip().splitlines() if out.strip() else [],
            "error": err.strip(),
        }

    def current_branch(self) -> str:
        rc, out, _ = self._run(["branch", "--show-current"])
        return out.strip() if rc == 0 else ""

    def last_commits(self, n: int = 5) -> list[str]:
        if n < 1 or n > 99:
            raise PermissionError("Neplatny limit commitov")
        rc, out, _ = self._run(["log", "--oneline", f"-{n}"])
        return out.strip().splitlines() if rc == 0 else []

    def is_clean(self) -> bool:
        s = self.status()
        return len(s.get("changes", [])) == 0

    def full_diagnostic(self) -> dict[str, Any]:
        return {
            "branch": self.current_branch(),
            "clean": self.is_clean(),
            "status": self.status(),
            "recent_commits": self.last_commits(5),
        }
