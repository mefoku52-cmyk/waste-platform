"""Ukladanie a obnova stavu po prerušení. Atomicky zápis, bezpečné načítanie."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path

from .models import TaskAssignment


class StateCorruptedError(Exception):
    """Stavovy subor je poskodeny alebo neplatny."""


class StateManager:
    """Spravuje stav systemu na disku. Atomicky zápis, bezpečné načítanie."""

    def __init__(self, state_dir: str | Path, authorize: Callable[[str], bool] | None = None):
        raw = Path(state_dir)
        # Odmietni symlink na adresar stavu (pred resolve)
        if raw.is_symlink():
            raise PermissionError("Adresar stavu je symbolicky odkaz")
        # Over, ze rodicovsky adresar nie je symlink
        if raw.parent.is_symlink():
            raise PermissionError("Rodicovsky adresar stavu je symbolicky odkaz")
        self.state_dir = raw.resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        # Nevolaj resolve() na state_file — zachovaj symlink pre O_NOFOLLOW kontrolu
        self.state_file = self.state_dir / "current_state.json"
        self._authorize = authorize or (lambda op: False)

    def _check_path(self, path: Path, root: Path | None = None) -> None:
        """Overí, že cieľ leží vnútri povoleného koreňového adresára.
        Kontroluje aj symlink rodičovského adresára."""
        allowed_root = (root or self.state_dir).resolve()
        # Over rodičovský adresár
        parent = path.parent.resolve() if path.parent.exists() else allowed_root
        if parent.is_symlink():
            raise PermissionError(f"Rodicovsky adresar je symbolicky odkaz: {parent}")
        resolved = path.resolve()
        try:
            resolved.relative_to(allowed_root)
        except ValueError:
            raise PermissionError(f"Zápis mimo povoleného adresára: {resolved}") from None

    def save(self, assignment: TaskAssignment) -> None:
        """Ulozi stav atomicky (tmp + replace). Chranene pred symlinkom a súbežným zápisom."""
        if not self._authorize("save"):
            raise PermissionError("Operacia 'save' nie je autorizovana")
        self._check_path(self.state_file)
        # Odmietni symlink na stavový súbor
        if self.state_file.is_symlink():
            raise PermissionError("Stavovy subor je symbolicky odkaz (zamietnute)")
        data = assignment.to_dict()
        content = json.dumps(data, indent=2, ensure_ascii=False)
        lock_path = self.state_dir / ".state.lock"
        with open(lock_path, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                fd, tmp_path = tempfile.mkstemp(dir=str(self.state_dir), suffix=".tmp")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        f.write(content)
                        f.flush()
                        os.fsync(f.fileno())
                    tmp = Path(tmp_path)
                    self._check_path(tmp)
                    os.replace(str(tmp), str(self.state_file))
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

    def load(self) -> TaskAssignment | None:
        """Nacita stav zo suboru. None ak neexistuje. Vyhodí StateCorruptedError pri poskodeni."""
        lock_path = self.state_dir / ".state.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_SH)
            try:
                if not self.state_file.exists():
                    return None
                flags = os.O_RDONLY
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                try:
                    fd = os.open(str(self.state_file), flags)
                except OSError:
                    raise StateCorruptedError("Nemozno otvorit stavovy subor")
                try:
                    info = os.fstat(fd)
                    if not __import__("stat").S_ISREG(info.st_mode):
                        raise StateCorruptedError("Stavovy subor nie je obycajny subor")
                    with os.fdopen(fd, "r", encoding="utf-8") as f:
                        raw = f.read()
                    data = json.loads(raw)
                    return TaskAssignment.from_dict(data)
                except (
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError,
                    OSError,
                    UnicodeDecodeError,
                ) as e:
                    raise StateCorruptedError(f"Stavovy subor je poskodeny: {type(e).__name__}")
                finally:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

    def clear(self) -> None:
        """Vymaze stav. Vyžaduje autorizaciu."""
        if not self._authorize("clear"):
            raise PermissionError("Operacia 'clear' nie je autorizovana")
        if self.state_file.exists():
            self.state_file.unlink()

    def exists(self) -> bool:
        return self.state_file.exists()

    def snapshot(self, label: str = "snapshot") -> Path:
        """Vytvori zalohu stavu. Vyžaduje autorizaciu."""
        if not self._authorize("snapshot"):
            raise PermissionError("Operacia 'snapshot' nie je autorizovana")
        if not self.state_file.exists():
            return Path()
        # Zálohy sú samostatný povolený koreň vedľa adresára stavov.
        backup_dir = (self.state_dir.parent / "zalohy").resolve()
        if not isinstance(label, str) or not label or label in {".", ".."}:
            raise ValueError("Neplatný názov zálohy")
        if Path(label).name != label or "/" in label or "\\\\" in label:
            raise ValueError("Názov zálohy nesmie obsahovať cestu")
        backup_dir.mkdir(parents=True, exist_ok=True)
        import time

        backup_path = backup_dir / f"{label}_{int(time.time())}.json"
        self._check_path(backup_path, backup_dir)
        # Bezpecne citanie state_file cez O_NOFOLLOW (povinne)
        if not hasattr(os, "O_NOFOLLOW"):
            raise StateCorruptedError("Platforma nepodporuje O_NOFOLLOW")
        try:
            fd = os.open(str(self.state_file), os.O_RDONLY | os.O_NOFOLLOW)
            info = os.fstat(fd)
            if not __import__("stat").S_ISREG(info.st_mode):
                raise StateCorruptedError("Stavovy subor nie je obycajny subor")
            with os.fdopen(fd, "r", encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            try:
                os.close(fd)
            except (OSError, UnboundLocalError):
                pass
            raise StateCorruptedError(f"Nemozno citat stavovy subor: {type(e).__name__}")
        backup_path.write_text(content, encoding="utf-8")
        return backup_path
