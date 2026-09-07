#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/list_real_routes_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== LIST REAL ROUTES ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

python3 - <<'PYEOF'
from app.main import create_app

app = create_app()

print("=== REGISTROVANE ROUTES ===")
for r in app.routes:
    path = getattr(r, "path", None)
    methods = getattr(r, "methods", None)
    name = getattr(r, "name", None)
    endpoint = getattr(r, "endpoint", None)
    endpoint_name = getattr(endpoint, "__name__", None) if endpoint else None

    if path is not None:
        print(f"PATH={path} | METHODS={sorted(methods) if methods else None} | NAME={name} | ENDPOINT={endpoint_name}")

print()
print("=== API ROUTES ONLY ===")
for r in app.routes:
    path = getattr(r, "path", None)
    methods = getattr(r, "methods", None)
    if isinstance(path, str) and path.startswith("/api"):
        print(f"{path} -> {sorted(methods) if methods else None}")

print()
print("=== HEALTH/METRICS FILTER ===")
for r in app.routes:
    path = getattr(r, "path", None)
    methods = getattr(r, "methods", None)
    if isinstance(path, str) and ("health" in path or "metrics" in path or "docs" in path or "openapi" in path):
        print(f"{path} -> {sorted(methods) if methods else None}")
PYEOF

echo
echo "REPORT: $REPORT"
echo "=== KONIEC LIST REAL ROUTES ==="
