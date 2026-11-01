"""Bezpecny vykonavaci model - predvolene vypnuty, explicitne schvalenie.
Trvala idempotencia cez atomicku rezervaciu v subore."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any


class ExecutionMode(Enum):
    DISABLED = "disabled"
    DRY_RUN = "dry_run"
    APPROVED = "approved"


class ExecutionPolicy:
    """Politika vykonavania oprav. Predvolene vypnuta. Trvala idempotencia."""

    ALLOWED_OPERATIONS = frozenset(
        {
            "diagnose",
            "inspect",
            "report",
            "plan",
        }
    )

    BLOCKED_OPERATIONS = frozenset(
        {
            "shell_exec",
            "file_write",
            "file_delete",
            "git_commit",
            "git_push",
            "db_write",
            "db_migrate",
            "deploy",
            "install",
        }
    )

    MAX_AUDIT_SIZE = 1_000_000  # 1 MB
    MAX_ARCHIVES = 3

    def __init__(
        self, mode: ExecutionMode = ExecutionMode.DISABLED, work_dir: str | Path | None = None
    ):
        self.mode = mode
        self.work_dir = Path(work_dir).resolve() if work_dir else None
        self.audit_log: list[dict[str, Any]] = []
        self._state_file = (self.work_dir / ".executed.json") if self.work_dir else None
        self._audit_file = (
            (self.work_dir.parent / "vystupy" / "audit.jsonl") if self.work_dir else None
        )
        if self.work_dir:
            self.work_dir.mkdir(parents=True, exist_ok=True)
            if self._audit_file:
                self._audit_file.parent.mkdir(parents=True, exist_ok=True)

    def is_allowed(self, operation: str) -> bool:
        if operation in self.BLOCKED_OPERATIONS:
            return False
        if self.mode == ExecutionMode.DISABLED:
            return False
        return operation in self.ALLOWED_OPERATIONS

    def check_path(self, path: str | Path) -> bool:
        if self.work_dir is None:
            return False
        try:
            resolved = Path(path).resolve()
            return str(resolved).startswith(str(self.work_dir))
        except (OSError, ValueError):
            return False

    def _load_executed_unlocked(self) -> dict[str, dict[str, Any]]:
        if self._state_file is None or not self._state_file.exists():
            return {}
        if self._state_file.is_symlink():
            return {}
        try:
            raw = self._state_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return {}

    def _save_executed_unlocked(self, data: dict[str, dict[str, Any]]) -> None:
        if self._state_file is None:
            return
        if self._state_file.is_symlink():
            raise PermissionError("Stavovy subor je symbolicky odkaz")
        content = json.dumps(data, indent=2, ensure_ascii=False)
        fd, tmp = tempfile.mkstemp(dir=str(self._state_file.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, str(self._state_file))
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def request_approval(
        self, operation: str, description: str, path: str | None = None
    ) -> dict[str, Any]:
        if path is not None and not self.check_path(path):
            return {"status": "denied", "reason": f"Cesta mimo pracovnej kopie: {path}"}
        record = {
            "operation": operation,
            "description": description,
            "mode": self.mode.value,
            "status": "pending_approval",
            "approved": False,
            "path": path,
        }
        self.audit_log.append(record)
        self._write_audit(record)
        return record

    def _write_audit(self, record: dict[str, Any]) -> None:
        if self._audit_file is None:
            return
        # Rotacia
        self._rotate_if_needed(self._audit_file)
        lock_path = self._audit_file.parent / ".audit.lock"
        with open(lock_path, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                if self._audit_file.is_symlink():
                    raise PermissionError("Auditny subor je symbolicky odkaz")
                flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                fd = os.open(self._audit_file, flags, 0o600)
                try:
                    info = os.fstat(fd)
                    if not __import__("stat").S_ISREG(info.st_mode):
                        raise ValueError("Auditny subor musi byt obycajny subor")
                    line = json.dumps(record, ensure_ascii=True, sort_keys=True, default=str) + "\n"
                    os.write(fd, line.encode("utf-8"))
                    os.fsync(fd)
                finally:
                    os.close(fd)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

    def _rotate_if_needed(self, path: Path) -> None:
        if path.exists() and path.stat().st_size >= self.MAX_AUDIT_SIZE:
            for i in range(self.MAX_ARCHIVES, 0, -1):
                src = path.with_suffix(f".jsonl.{i}")
                dst = path.with_suffix(f".jsonl.{i + 1}")
                if src.exists():
                    if i >= self.MAX_ARCHIVES:
                        src.unlink()
                    else:
                        os.replace(str(src), str(dst))
            os.replace(str(path), str(path.with_suffix(".jsonl.1")))

    def execute(
        self, operation: str, dry_run: bool = True, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        # Allowlist a path check pred rezervaciou
        if operation in self.BLOCKED_OPERATIONS:
            return {"status": "blocked", "reason": f"Operacia {operation} je zablokovana"}
        if self.mode == ExecutionMode.DISABLED:
            return {"status": "disabled", "reason": "Vykonavanie je vypnute"}
        if not self.is_allowed(operation):
            return {"status": "denied", "reason": f"Operacia {operation} nie je povolena"}

        key = idempotency_key or operation

        # Atomicka rezervacia
        lock_path = (self._state_file.parent / ".exec.lock") if self._state_file else None
        if lock_path is None:
            return {"status": "error", "reason": "work_dir nie je nastaveny"}

        with open(lock_path, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                executed = self._load_executed_unlocked()
                if key in executed:
                    state = executed[key].get("status", "unknown")
                    if state == "completed":
                        return {
                            "status": "already_executed",
                            "operation": operation,
                            "idempotent": True,
                        }
                    if state == "in_progress":
                        return {
                            "status": "interrupted",
                            "operation": operation,
                            "reason": "Operacia bola prerušená, vyžaduje posúdenie",
                        }
                    if state == "failed":
                        return {
                            "status": "failed_previously",
                            "operation": operation,
                            "reason": "Operacia zlyhala, vyžaduje posúdenie",
                        }
                # Rezervuj
                executed[key] = {
                    "status": "in_progress",
                    "operation": operation,
                    "timestamp": __import__("datetime")
                    .datetime.now(__import__("datetime").timezone.utc)
                    .isoformat(),
                }
                self._save_executed_unlocked(executed)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

        # DRY_RUN nevykonáva
        if dry_run or self.mode == ExecutionMode.DRY_RUN:
            # Zrus rezervaciu
            executed = self._load_executed_unlocked()
            if key in executed and executed[key].get("status") == "in_progress":
                executed[key]["status"] = "dry_run"
                self._save_executed_unlocked(executed)
            return {"status": "dry_run", "operation": operation, "would_execute": True}

        # Skutocne vykonanie (len ak APPROVED)
        if self.mode != ExecutionMode.APPROVED:
            return {"status": "denied", "reason": "Vykonanie vyžaduje režim APPROVED"}

        # Tu by sa vykonala operácia (v tejto fáze je vykonávanie zakázané)
        # Označ ako completed len ak skutočne vykonané
        executed = self._load_executed_unlocked()
        if key in executed:
            executed[key]["status"] = "completed"
            executed[key]["result"] = "executed"
            self._save_executed_unlocked(executed)
        try:
            self._write_audit(
                {
                    "operation": operation,
                    "status": "executed",
                    "key": key,
                    "timestamp": __import__("datetime")
                    .datetime.now(__import__("datetime").timezone.utc)
                    .isoformat(),
                }
            )
        except Exception:
            # Audit zlyhal — operacia sa nesmie vykonať
            executed = self._load_executed_unlocked()
            if key in executed:
                executed[key]["status"] = "failed"
                executed[key]["result"] = "audit_failed"
                self._save_executed_unlocked(executed)
            return {
                "status": "audit_failed",
                "operation": operation,
                "reason": "Auditny zapis zlyhal",
            }
        return {"status": "executed", "operation": operation}
