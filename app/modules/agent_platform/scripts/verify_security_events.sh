#!/usr/bin/env bash
set -euo pipefail
ROOT="\( (cd " \)(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
mod = Path("app/modules/agent_platform")
need = [
    "application/security/security_engine.py",
    "infrastructure/security/security_event_store.py",
    "application/alerts/alert_service.py",
    "application/audit/audit_service.py",
]
missing = [n for n in need if not (mod / n).exists()]
if missing:
    raise SystemExit("MISSING " + ",".join(missing))
print("SECURITY_EVENTS_OK")
PY
