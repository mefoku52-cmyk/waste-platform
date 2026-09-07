#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/compare_frontend_backend_api_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== COMPARE FRONTEND BACKEND API ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

echo "## BACKEND ROUTE SIGNALS"
python3 - <<'PYEOF'
import sys
from pathlib import Path

project = Path.home() / "waste-platform"
sys.path.insert(0, str(project))

from app.main import create_app

app = create_app()

for r in app.routes:
    if type(r).__name__ != "_IncludedRouter":
        continue
    orig = getattr(r, "original_router", None)
    ctx = getattr(r, "include_context", None)
    prefix = getattr(ctx, "prefix", "") if ctx else ""
    if not orig:
        continue
    for nr in getattr(orig, "routes", []) or []:
        path = getattr(nr, "path", None)
        methods = getattr(nr, "methods", None)
        if path:
            print(f"{prefix}{path} :: {sorted(methods) if methods else None}")
PYEOF
echo

echo "## FRONTEND API CALL SIGNALS"
grep -RniE '/api/v1/|fetch\(|axios|ky\.|api/' "$PROJECT/apps/web/src" \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' 2>/dev/null || true
echo

echo "## FRONTEND FEATURE TREE"
find "$PROJECT/apps/web/src/features" -maxdepth 2 -type f 2>/dev/null | sed "s|$PROJECT|.|" | sort
echo

echo "REPORT: $REPORT"
echo "=== KONIEC COMPARE FRONTEND BACKEND API ==="
