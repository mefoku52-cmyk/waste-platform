#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/build_project_manifest_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== BUILD PROJECT MANIFEST ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

python3 - <<'PYEOF'
import sys
from pathlib import Path

project = Path.home() / "waste-platform"
sys.path.insert(0, str(project))

from app.main import create_app

app = create_app()

print("## BACKEND MODULE MANIFEST")
for r in app.routes:
    if type(r).__name__ != "_IncludedRouter":
        continue
    orig = getattr(r, "original_router", None)
    ctx = getattr(r, "include_context", None)
    prefix = getattr(ctx, "prefix", None) if ctx else None
    if not orig:
        continue
    routes = getattr(orig, "routes", []) or []
    if not routes:
        continue

    first = routes[0]
    base = getattr(first, "path", None)
    print(f"MODULE_PREFIX={prefix!r} FIRST_PATH={base!r} ROUTE_COUNT={len(routes)}")

    for nr in routes:
        path = getattr(nr, "path", None)
        name = getattr(nr, "name", None)
        methods = getattr(nr, "methods", None)
        print(f"  - PATH={path!r} METHODS={sorted(methods) if methods else None} NAME={name!r}")
    print()
PYEOF

echo "## FRONTEND TREE"
find "$PROJECT/apps/web" -maxdepth 3 \
  \( -path '*/.next' -o -path '*/node_modules' -o -path '*/dist' -o -path '*/build' \) -prune \
  -o -print 2>/dev/null | sed "s|$PROJECT|.|" | sort
echo

echo "## TEST FILES"
find "$PROJECT/tests" "$PROJECT/app/tests" -type f 2>/dev/null | sed "s|$PROJECT|.|" | sort
echo

echo "## ROOT AUDIT ARTIFACTS"
find "$PROJECT" -maxdepth 1 -type f \( -name '*.txt' -o -name '*.sh' \) | sed "s|$PROJECT|.|" | sort
echo

echo "## ROOT RISK FILES"
find "$PROJECT" -maxdepth 1 -type f \( -size 0c -o -name 'dump.rdb' -o -name 'lookup_website.html' \) | sed "s|$PROJECT|.|" | sort
echo

echo "REPORT: $REPORT"
echo "=== KONIEC BUILD PROJECT MANIFEST ==="
