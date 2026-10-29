"""Bezpečný lokálny denník monitorovacích udalostí CMEP."""

import fcntl
import hashlib
import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _fingerprint(snapshot: dict[str, Any]) -> str:
    git = snapshot.get("git") or {}
    status = git.get("status") or {}
    site = snapshot.get("site") or {}
    stable = {
        "branch": git.get("branch"),
        "clean": git.get("clean"),
        "changes": sorted(status.get("changes", []))
        if isinstance(status.get("changes"), list)
        else None,
        "git_error": bool(git.get("error")),
        "site_ok": site.get("ok"),
        "site_status": site.get("status"),
        "site_error": bool(site.get("error")),
    }
    data = json.dumps(stable, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def incident_record(
    snapshot: dict[str, Any],
    previous: str | None = None,
    previous_site_ok: bool | None = None,
) -> dict[str, Any]:
    """Záznam bez tela HTTP, výpisu commitov a obsahu jednotlivých zmien."""
    git = snapshot.get("git") or {}
    status = git.get("status") or {}
    site = snapshot.get("site") or {}
    changes = status.get("changes")
    fingerprint = _fingerprint(snapshot)

    site = snapshot.get("site") or {}
    current_site_ok = site.get("ok") if isinstance(site.get("ok"), bool) else None
    if previous is None:
        event = "baseline"
    elif fingerprint == previous:
        event = "inspection"
    elif previous_site_ok is False and current_site_ok is True:
        event = "resolved"
    else:
        event = "change_detected"
    branch = git.get("branch")
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        "fingerprint": fingerprint,
        "git": {
            "branch": branch[:120] if isinstance(branch, str) else None,
            "clean": git.get("clean") if isinstance(git.get("clean"), bool) else None,
            "change_count": len(changes) if isinstance(changes, list) else None,
            "error": bool(git.get("error")),
        },
        "site": {
            "ok": site.get("ok") if isinstance(site.get("ok"), bool) else None,
            "status": site.get("status") if isinstance(site.get("status"), int) else None,
            "error": bool(site.get("error")),
        },
    }


def read_incidents(path: str | Path) -> list[dict[str, Any]]:
    """Bezpečne prečíta JSONL denník. Preskakuje poškodené riadky bez zmazania histórie."""
    target = Path(path).expanduser()
    lock_path = target.parent / ".incident.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_SH)
        try:
            if not target.exists():
                return []
            flags = os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                fd = os.open(str(target), flags)
            except OSError:
                return []  # Chyba prístupu — nie prázdny denník
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    return []
                with os.fdopen(fd, "r", encoding="utf-8") as f:
                    results = []
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            results.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue  # Poškodený riadok — preskočiť, nie zmazať
                    return results
            except OSError:
                return []
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def append_incident(path: str | Path, record: dict[str, Any]) -> None:
    """Pridá jeden JSONL záznam; odmieta symbolický odkaz na cieľový súbor."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    lock_path = target.parent / ".incident.lock"
    with open(lock_path, "w") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            # Rotacia pri dosiahnuti limitu (1 MB, max 3 archivy)
            # Chyba rotacie sa NESMIE potichu ignorovat — propaguje sa
            if target.exists() and target.stat().st_size >= 1_000_000:
                try:
                    for i in range(3, 0, -1):
                        src_f = target.with_suffix(f".jsonl.{i}")
                        dst_f = target.with_suffix(f".jsonl.{i + 1}")
                        if src_f.exists():
                            if i >= 3:
                                src_f.unlink()
                            else:
                                os.replace(str(src_f), str(dst_f))
                    os.replace(str(target), str(target.with_suffix(".jsonl.1")))
                except OSError as exc:
                    raise RuntimeError(f"Rotacia dennika zlyhala: {exc}") from exc
            fd = os.open(target, flags, 0o600)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("Denník musí byť obyčajný súbor")
                line = json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n"
                os.write(fd, line.encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
