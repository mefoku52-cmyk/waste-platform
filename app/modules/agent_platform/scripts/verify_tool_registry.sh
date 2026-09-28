#!/usr/bin/env bash
set -euo pipefail
ROOT="\( (cd " \)(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p = Path("app/modules/agent_platform/infrastructure/tools")
need = [
    "tool_catalog.py",
    "forbidden_tool_names.py",
    "safe_tool_registry.py",
    "cmep_tool_dispatcher.py",
]
missing = [n for n in need if not (p / n).exists()]
if missing:
    raise SystemExit("MISSING " + ",".join(missing))
print("TOOL_REGISTRY_OK")
PY
