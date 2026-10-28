"""Spustenie nepretrziteho read-only monitorovania CMEP."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .execution_policy import ExecutionMode, ExecutionPolicy
from .incident_log import append_incident, incident_record
from .monitor import (
    DEFAULT_URL,
    MAX_INTERVAL,
    MIN_INTERVAL,
    collect_snapshot,
    emit,
    run_monitor,
    validate_url,
)
from .permissions import PermissionPolicy
from .state import StateManager


def _state_dir() -> Path:
    return Path.home() / "cmep-riadiaci-system" / "stav"


def _incident_log_path() -> Path:
    return Path.home() / "cmep-riadiaci-system" / "vystupy" / "incidents.jsonl"


def cmd_once(args) -> int:
    try:
        validate_url(args.url)
    except ValueError as exc:
        print(f"ZAMIETNUTÉ: {exc}", file=sys.stderr)
        return 2
    snap = collect_snapshot(args.repo, args.url)
    emit("inspection", snap)
    # Zapis do incident logu
    try:
        rec = incident_record(snap, None)
        append_incident(str(_incident_log_path()), rec)
    except Exception as exc:
        print(f"CHYBA zápisu denníka: {type(exc).__name__}", file=sys.stderr)
    return 0


def cmd_run(args) -> int:
    try:
        return run_monitor(
            repo_path=args.repo,
            url=args.url,
            interval=args.interval,
            max_cycles=args.max_cycles,
            state_dir=str(_state_dir()),
            incident_log_path=str(_incident_log_path()),
        )
    except ValueError as exc:
        print(f"ZAMIETNUTÉ: {exc}", file=sys.stderr)
        return 2


def cmd_status(args) -> int:
    sm = StateManager(_state_dir(), authorize=lambda op: True)
    assignment = sm.load()
    if assignment is None:
        print("Žiadny trvalý stav monitorovania.")
        return 0
    print(f"Zadanie: {assignment.title}")
    print(f"Ulohy: {len(assignment.tasks)}")
    for t in assignment.tasks:
        print(f"  [{t.status.value}] {t.id[:8]} {t.title} (prio={t.priority.value})")
    # Posledny odtlacok
    for t in assignment.tasks:
        if t.metadata.get("type") == "monitor_fingerprint":
            print(f"Posledný odtlačok: {t.metadata.get('fingerprint')}")
    return 0


def cmd_incidents(args) -> int:
    path = _incident_log_path()
    if not path.exists():
        print("Žiadny denník incidentov.")
        return 0
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    print(f"Incidenty: {len(lines)}")
    for line in lines[-(args.last or 10) :]:
        try:
            rec = json.loads(line)
            print(
                f"  {rec.get('timestamp')} | {rec.get('event')} | site={rec.get('site', {}).get('status')} | changes={rec.get('git', {}).get('change_count')}"
            )
        except json.JSONDecodeError:
            print("  [poskodeny riadok]")
    return 0


def cmd_tasks(args) -> int:
    sm = StateManager(_state_dir(), authorize=lambda op: True)
    assignment = sm.load()
    if assignment is None:
        print("Žiadne úlohy.")
        return 0
    open_tasks = [
        t for t in assignment.tasks if t.status.value in ("planned", "in_progress", "blocked")
    ]
    print(f"Otvorené diagnostické úlohy: {len(open_tasks)}")
    for t in open_tasks:
        print(f"  [{t.status.value}] {t.id[:8]} {t.title}")
    return 0


def cmd_propose_fix(args) -> int:
    print("Návrh opravy (dry-run, žiadna oprava sa nevykoná):")
    print(f"  Operácia: {args.operation}")
    print(f"  Popis: {args.description}")
    ep = ExecutionPolicy(mode=ExecutionMode.DRY_RUN)
    result = ep.execute(args.operation, dry_run=True)
    print(f"  Výsledok: {result}")
    print("  Vyžaduje explicitné schválenie pred vykonaním.")
    return 0


def cmd_permissions(args) -> int:
    policy = PermissionPolicy()
    op = args.operation
    allowed = policy.is_allowed(op)
    print(f"Operácia '{op}': {'POVOLENÁ' if allowed else 'ZAMIETNUTÁ'}")
    print(f"Režim: {policy.mode.value}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cmep-monitor",
        description="Nepretrzita diagnostika CMEP bez automatickych oprav",
    )
    parser.add_argument(
        "--interval", type=int, default=30, help="Interval v sekundach (5-3600, predvolene 30)"
    )
    parser.add_argument("--once", action="store_true", help="Vykonaj iba jeden diagnosticky cyklus")
    parser.add_argument(
        "--max-cycles", type=int, default=None, help="Ukonci monitor po danom pocte cyklov"
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("CMEP_HEALTH_URL", DEFAULT_URL),
        help="HTTPS adresa verejnej stranky",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("CMEP_REPO", str(Path.home() / "waste-platform")),
        help="Cesta k CMEP Git repozitaru",
    )

    sub = parser.add_subparsers(dest="subcommand")
    sub.add_parser("run", help="Spusti monitorovaci cyklus")
    sub.add_parser("once", help="Jednorazova kontrola")
    sub.add_parser("status", help="Zobraz stav monitorovania")
    p_inc = sub.add_parser("incidents", help="Zobraz incidenty")
    p_inc.add_argument("--last", type=int, default=10, help="Pocet poslednych incidentov")
    sub.add_parser("tasks", help="Zobraz otvorene diagnostické úlohy")
    p_pf = sub.add_parser("propose-fix", help="Vytvor návrh opravy (dry-run)")
    p_pf.add_argument("operation", help="Nazov operacie")
    p_pf.add_argument("description", help="Popis návrhu")
    p_perm = sub.add_parser("permissions", help="Zobraz oprávnenia operacie")
    p_perm.add_argument("operation", help="Nazov operacie")

    args = parser.parse_args()

    if args.subcommand is None:
        # Backward compat: --once or run
        if not MIN_INTERVAL <= args.interval <= MAX_INTERVAL:
            parser.error("interval musi byt v rozsahu 5-3600 sekund")
        if args.max_cycles is not None and args.max_cycles < 1:
            parser.error("--max-cycles musi byt aspon 1")
        if args.once and args.max_cycles is not None:
            parser.error("--once a --max-cycles sa nesmu kombinovat")
        if args.once:
            return cmd_once(args)
        return cmd_run(args)

    if args.subcommand == "run":
        if not MIN_INTERVAL <= args.interval <= MAX_INTERVAL:
            parser.error("interval musi byt v rozsahu 5-3600 sekund")
        return cmd_run(args)
    if args.subcommand == "once":
        return cmd_once(args)
    if args.subcommand == "status":
        return cmd_status(args)
    if args.subcommand == "incidents":
        return cmd_incidents(args)
    if args.subcommand == "tasks":
        return cmd_tasks(args)
    if args.subcommand == "propose-fix":
        return cmd_propose_fix(args)
    if args.subcommand == "permissions":
        return cmd_permissions(args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
