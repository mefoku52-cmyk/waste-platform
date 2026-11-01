"""CLI pre riadiaci system CMEP."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Config
from .git_diag import GitDiagnostic
from .permissions import PermissionPolicy
from .planner import Planner
from .state import StateManager


def _base_dir() -> Path:
    return Path.home() / "cmep-riadiaci-system"


def cmd_init(args):
    print("ZAMIETNUTÉ: init vytvára adresáre a vyžaduje výslovné povolenie zápisu.")
    return 2
    sm = StateManager(cfg.state_dir)
    print(f"Init OK. Adresar: {cfg.base_dir}")
    print(f"Stavovy subor: {sm.state_file}")
    return 0


def cmd_status(args):
    cfg = Config()
    sm = StateManager(cfg.state_dir)
    assignment = sm.load()
    if assignment is None:
        print("Ziadny aktivny stav.")
        return 0
    print(f"Zadanie: {assignment.title}")
    print(f"Ulohy: {len(assignment.tasks)}")
    for t in assignment.tasks:
        print(
            f"  [{t.status.value}] {t.id[:8]} {t.title} (prio={t.priority.value}, risk={t.risk.value})"
        )
    return 0


def cmd_plan(args):
    cfg = Config()
    sm = StateManager(cfg.state_dir)
    assignment = sm.load()
    if assignment is None:
        print("Ziadny stav na planovanie.")
        return 1
    planner = Planner(assignment.tasks)
    ok, msg = planner.validate()
    if not ok:
        print(f"PLAN NEPLATNY: {msg}")
        return 1
    ready = planner.get_ready()
    blocked = planner.get_blocked()
    print(f"Plan OK. Pripravene: {len(ready)}, Blokovane: {len(blocked)}")
    for t in ready:
        print(f"  READY: {t.id[:8]} {t.title}")
    for t in blocked:
        print(f"  BLOCKED: {t.id[:8]} {t.title}")
    return 0


def cmd_inspect(args):
    cfg = Config()
    gd = GitDiagnostic(cfg.cmep_repo)
    diag = gd.full_diagnostic()
    print(json.dumps(diag, indent=2, ensure_ascii=False))
    return 0


def cmd_resume(args):
    cfg = Config()
    sm = StateManager(cfg.state_dir)
    assignment = sm.load()
    if assignment is None:
        print("Ziadny stav na obnovenie.")
        return 1
    print(f"Obnovene zadanie: {assignment.title}")
    print(f"Ulohy: {len(assignment.tasks)}")
    # Nedokoncene ulohy zostavaju nedokoncene
    for t in assignment.tasks:
        if t.status.value == "completed":
            print(f"  [completed] {t.id[:8]} {t.title}")
        else:
            print(f"  [{t.status.value}] {t.id[:8]} {t.title} (NEZMENENE)")
    return 0


def cmd_report(args):
    print("ZAMIETNUTÉ: report zapisuje súbor a nie je povolený v režime iba čítania.")
    return 2
    assignment = sm.load()
    if assignment is None:
        print("Ziadny stav na report.")
        return 1
    out = cfg.output_dir / "report.json"
    out.write_text(json.dumps(assignment.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report ulozeny: {out}")
    return 0


def cmd_check(args):
    cfg = Config()
    policy = PermissionPolicy()
    print("Bezpecnostna kontrola:")
    print(f"  Rezim: {policy.mode.value}")
    print(f"  Zakazane operacie: {len(policy.FORBIDDEN_OPERATIONS)}")
    # Test git read-only
    gd = GitDiagnostic(cfg.cmep_repo)
    diag = gd.full_diagnostic()
    print(f"  CMEP vetva: {diag['branch']}")
    print(f"  CMEP cisty: {diag['clean']}")
    print("  OK - iba citanie")
    return 0


def cmd_monitor_once(args):
    from .monitor import run_monitor

    rc = run_monitor(
        repo_path=args.repo,
        url=args.url,
        interval=5,
        max_cycles=1,
        state_dir=str(Path.home() / "cmep-riadiaci-system" / "stav"),
        incident_log_path=str(Path.home() / "cmep-riadiaci-system" / "vystupy" / "incidents.jsonl"),
    )
    return rc


def cmd_monitor_status(args):
    from .state import StateManager

    sm = StateManager(Path.home() / "cmep-riadiaci-system" / "stav", authorize=lambda op: True)
    assignment = sm.load()
    if assignment is None:
        print("Žiadny trvalý stav monitorovania.")
        return 0
    print(f"Zadanie: {assignment.title}")
    print(f"Ulohy: {len(assignment.tasks)}")
    for t in assignment.tasks:
        print(f"  [{t.status.value}] {t.id[:8]} {t.title}")
    return 0


def cmd_incidents(args):
    log_path = Path.home() / "cmep-riadiaci-system" / "vystupy" / "incidents.jsonl"
    if not log_path.exists():
        print("Žiadny denník incidentov.")
        return 0
    import json

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    print(f"Incidenty: {len(lines)}")
    for line in lines[-10:]:
        try:
            rec = json.loads(line)
            print(
                f"  {rec.get('timestamp')} | {rec.get('event')} | site={rec.get('site', {}).get('status')}"
            )
        except json.JSONDecodeError:
            print("  [poskodeny riadok]")
    return 0


def cmd_diagnostic_tasks(args):
    from .state import StateManager

    sm = StateManager(Path.home() / "cmep-riadiaci-system" / "stav", authorize=lambda op: True)
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


def cmd_propose_fix(args):
    from .execution_policy import ExecutionMode, ExecutionPolicy

    print("Návrh opravy (dry-run, žiadna oprava sa nevykoná):")
    ep = ExecutionPolicy(mode=ExecutionMode.DRY_RUN)
    result = ep.execute(args.operation, dry_run=True)
    print(f"  Operácia: {args.operation}")
    print(f"  Výsledok: {result}")
    print("  Vyžaduje explicitné schválenie pred vykonaním.")
    return 0


def cmd_permissions(args):
    from .permissions import PermissionPolicy

    policy = PermissionPolicy()
    op = args.operation
    allowed = policy.is_allowed(op)
    print(f"Operácia '{op}': {'POVOLENÁ' if allowed else 'ZAMIETNUTÁ'}")
    print(f"Režim: {policy.mode.value}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="cmep-riadenie", description="Riadiaci system CMEP (iba citanie)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Inicializacia")
    sub.add_parser("status", help="Stav systemu")
    sub.add_parser("plan", help="Planovanie uloh")
    sub.add_parser("inspect", help="Diagnostika CMEP (read-only)")
    sub.add_parser("resume", help="Obnova stavu")
    sub.add_parser("report", help="Vygenerovanie reportu")
    sub.add_parser("check", help="Bezpecnostna kontrola")

    p_mo = sub.add_parser("monitor-once", help="Jednorazova kontrola monitora")
    p_mo.add_argument("--url", default="https://trc-cmep.sk", help="HTTPS adresa")
    p_mo.add_argument(
        "--repo", default=str(Path.home() / "waste-platform"), help="Cesta k repozitaru"
    )

    sub.add_parser("monitor-status", help="Stav monitorovania")
    sub.add_parser("incidents", help="Zobraz incidenty")
    sub.add_parser("diagnostic-tasks", help="Zobraz diagnostické úlohy")

    p_pf = sub.add_parser("propose-fix", help="Vytvor návrh opravy (dry-run)")
    p_pf.add_argument("operation", help="Nazov operacie")
    p_pf.add_argument("description", nargs="?", default="", help="Popis")

    p_perm = sub.add_parser("permissions", help="Zobraz oprávnenia operacie")
    p_perm.add_argument("operation", help="Nazov operacie")

    args = parser.parse_args()
    commands = {
        "init": cmd_init,
        "status": cmd_status,
        "plan": cmd_plan,
        "inspect": cmd_inspect,
        "resume": cmd_resume,
        "report": cmd_report,
        "check": cmd_check,
        "monitor-once": cmd_monitor_once,
        "monitor-status": cmd_monitor_status,
        "incidents": cmd_incidents,
        "diagnostic-tasks": cmd_diagnostic_tasks,
        "propose-fix": cmd_propose_fix,
        "permissions": cmd_permissions,
    }
    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()
