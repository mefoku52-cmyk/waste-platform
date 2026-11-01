"""Bezpecny monitor CMEP: iba citanie, bez automatickych oprav."""

from __future__ import annotations

import fcntl
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .git_diag import GitDiagnostic
from .incident_log import append_incident, incident_record
from .models import RiskLevel, TaskPriority, TaskStatus
from .state import StateManager
from .task_intake import TaskIntake

MIN_INTERVAL = 5
MAX_INTERVAL = 3600
DEFAULT_URL = "https://trc-cmep.sk"


def validate_url(url: str) -> str:
    """Povoli iba bezpecnu URL bez prihlasovacich udajov a query tokenov."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "URL musi pouzivat HTTPS a nesmie obsahovat prihlasovacie udaje, query ani fragment"
        )
    return url


def check_site(url: str = DEFAULT_URL, timeout: float = 8.0) -> dict[str, Any]:
    """Vykona iba HTTP GET; nevracia telo stranky ani detaily chyb."""
    validate_url(url)
    started = time.monotonic()
    request = Request(
        url,
        headers={"User-Agent": "CMEP-ReadOnly-Monitor/1.0"},
        method="GET",
    )

    status = None
    error = None
    try:
        with urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            response.read(0)
    except HTTPError as exc:
        status = int(exc.code)
        error = "HTTPError"
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        # Nepíšeme surovú chybu, URL ani možné citlivé údaje.
        error = type(exc).__name__

    elapsed_ms = round((time.monotonic() - started) * 1000)
    return {
        "ok": status is not None and 200 <= status < 400,
        "status": status,
        "elapsed_ms": elapsed_ms,
        "error": error,
    }


def collect_snapshot(repo_path: str, url: str = DEFAULT_URL) -> dict[str, Any]:
    """Zbiera stav repozitara a dostupnost webu. Nevykonava opravy."""
    try:
        git = GitDiagnostic(repo_path).full_diagnostic()
        git_error = None
    except Exception as exc:
        git = {}
        git_error = type(exc).__name__

    try:
        site = check_site(url)
    except Exception as exc:
        site = {
            "ok": False,
            "status": None,
            "elapsed_ms": 0,
            "error": type(exc).__name__,
        }

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git": git,
        "git_error": git_error,
        "site": site,
    }


def fingerprint(snapshot: dict[str, Any]) -> str:
    """Porovnava stav, nie cas merania alebo kolisanie odozvy."""
    git = snapshot.get("git") or {}
    site = snapshot.get("site") or {}
    stable = {
        "git_branch": git.get("branch"),
        "git_clean": git.get("clean"),
        "git_status": git.get("status"),
        "git_error": snapshot.get("git_error"),
        "site_ok": site.get("ok"),
        "site_status": site.get("status"),
        "site_error": site.get("error"),
    }
    encoded = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def emit(event: str, snapshot: dict[str, Any]) -> None:
    """Vypise jeden strojovo citatelny JSON riadok na stdout."""
    print(
        json.dumps(
            {"event": event, "snapshot": snapshot},
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ),
        flush=True,
    )


def _load_previous_fingerprint(state_dir: str) -> str | None:
    try:
        sm = StateManager(state_dir, authorize=lambda op: True)
        assignment = sm.load()
        if assignment is None:
            return None
        for t in assignment.tasks:
            if t.metadata.get("type") == "monitor_fingerprint":
                return t.metadata.get("fingerprint")
    except Exception:
        return None
    return None


def _load_previous_site_ok(state_dir: str) -> bool | None:
    try:
        sm = StateManager(state_dir, authorize=lambda op: True)
        assignment = sm.load()
        if assignment is None:
            return None
        for t in assignment.tasks:
            if t.metadata.get("type") == "monitor_fingerprint":
                v = t.metadata.get("site_ok")
                return v if isinstance(v, bool) else None
    except Exception:
        return None
    return None


def _save_fingerprint(state_dir: str, fp: str, snapshot: dict) -> None:
    try:
        sm = StateManager(state_dir, authorize=lambda op: True)
        assignment = sm.load()
        if assignment is None:
            ti = TaskIntake()
            assignment = ti.accept("Monitor stav", "Trvaly stav monitorovania CMEP")
        found = False
        for t in assignment.tasks:
            if t.metadata.get("type") == "monitor_fingerprint":
                t.metadata["fingerprint"] = fp
                t.metadata["site_ok"] = (snapshot.get("site") or {}).get("ok")
                found = True
                break
        if not found:
            ti = TaskIntake()
            task = ti.create_task(
                title="Monitor odtlacok",
                description="Posledny platny odtlacok monitorovania",
                priority=TaskPriority.LOW,
                risk=RiskLevel.LOW,
            )
            task.metadata["type"] = "monitor_fingerprint"
            task.metadata["fingerprint"] = fp
            task.metadata["site_ok"] = (snapshot.get("site") or {}).get("ok")
            task.status = TaskStatus.COMPLETED
            assignment.tasks.append(task)
        sm.save(assignment)
    except Exception:
        pass


def _create_diagnostic_task(state_dir: str, snapshot: dict, event: str) -> None:
    try:
        sm = StateManager(state_dir, authorize=lambda op: True)
        assignment = sm.load()
        if assignment is None:
            ti = TaskIntake()
            assignment = ti.accept("Monitor incidenty", "Diagnostické úlohy z monitorovania")
        fp = fingerprint(snapshot)
        for t in assignment.tasks:
            if t.metadata.get("incident_fingerprint") == fp and t.status.value in (
                "planned",
                "in_progress",
                "blocked",
            ):
                return
        ti = TaskIntake()
        task = ti.create_task(
            title=f"Diagnostika: {event}",
            description=f"Monitor zistil udalost {event}. Vyžaduje diagnostiku a návrh opravy.",
            priority=TaskPriority.HIGH,
            risk=RiskLevel.MEDIUM,
            criteria=["Preverit pricinu", "Navrhnut opravu", "Schvalit opravu pred vykonanim"],
        )
        task.metadata["incident_fingerprint"] = fp
        task.metadata["incident_event"] = event
        assignment.tasks.append(task)
        sm.save(assignment)
    except Exception:
        pass


def _acquire_monitor_lock(state_dir: str) -> object | None:
    """Získa zámok proti súbežnému spusteniu viacerých monitorov."""
    lock_path = Path(state_dir) / ".monitor.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lockf = open(lock_path, "w")
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lockf
    except OSError:
        return None


def _release_monitor_lock(lockf) -> None:
    if lockf is not None:
        try:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
            lockf.close()
        except OSError:
            pass


def run_monitor(
    repo_path: str,
    url: str = DEFAULT_URL,
    interval: int = 30,
    max_cycles: int | None = None,
    state_dir: str | None = None,
    incident_log_path: str | None = None,
) -> int:
    """Monitoruje, hlasi zmeny a skonci po limite alebo cez Ctrl+C."""
    if not MIN_INTERVAL <= interval <= MAX_INTERVAL:
        raise ValueError(f"Interval musi byt {MIN_INTERVAL} az {MAX_INTERVAL} sekund")
    if max_cycles is not None and max_cycles < 1:
        raise ValueError("max_cycles musi byt aspon 1")

    if state_dir is None:
        state_dir = str(Path.home() / "cmep-riadiaci-system" / "stav")
    if incident_log_path is None:
        incident_log_path = str(Path(state_dir).parent / "vystupy" / "incidents.jsonl")

    lockf = _acquire_monitor_lock(state_dir)
    if lockf is None:
        print('{"event":"error","reason":"monitor_already_running"}', flush=True)
        return 1

    previous = _load_previous_fingerprint(state_dir)
    cycle = 0

    try:
        while max_cycles is None or cycle < max_cycles:
            snapshot = collect_snapshot(repo_path, url)
            current = fingerprint(snapshot)
            cycle += 1

            try:
                prev_site = _load_previous_site_ok(state_dir)
                rec = incident_record(snapshot, previous, prev_site)
                append_incident(incident_log_path, rec)
            except Exception:
                pass

            if previous is None:
                emit("baseline", snapshot)
                _create_diagnostic_task(state_dir, snapshot, "baseline")
            elif current != previous:
                emit("change_detected", snapshot)
                _create_diagnostic_task(state_dir, snapshot, "change_detected")
            elif cycle % 12 == 0:
                emit("heartbeat", snapshot)

            previous = current
            _save_fingerprint(state_dir, current, snapshot)

            if max_cycles is not None and cycle >= max_cycles:
                break
            time.sleep(interval)

    except KeyboardInterrupt:
        print('{"event":"stopped","reason":"keyboard_interrupt"}', flush=True)
    finally:
        _release_monitor_lock(lockf)

    return 0
