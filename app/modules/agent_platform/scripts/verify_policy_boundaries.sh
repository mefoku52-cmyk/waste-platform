#!/usr/bin/env bash
set -euo pipefail
ROOT="\( (cd " \)(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
mod = Path("app/modules/agent_platform")
need = [
    "application/policy/policy_engine.py",
    "application/permission/permission_engine.py",
    "application/approval/approval_service.py",
]
missing = [n for n in need if not (mod / n).exists()]
if missing:
    raise SystemExit("MISSING " + ",".join(missing))
print("POLICY_BOUNDARIES_OK")
PY
