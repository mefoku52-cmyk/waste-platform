#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/inspect_route_objects_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== INSPECT ROUTE OBJECTS ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

python3 - <<'PYEOF'
from app.main import create_app

app = create_app()

print("=== APP ROUTES DETAIL ===")
for i, r in enumerate(app.routes, 1):
    cls = type(r).__name__
    path = getattr(r, "path", None)
    name = getattr(r, "name", None)
    methods = getattr(r, "methods", None)
    endpoint = getattr(r, "endpoint", None)
    endpoint_name = getattr(endpoint, "__name__", None) if endpoint else None

    print(f"[{i}] CLASS={cls}")
    print(f"    path={path!r}")
    print(f"    name={name!r}")
    print(f"    methods={sorted(methods) if methods else None}")
    print(f"    endpoint={endpoint_name!r}")

    routes_attr = getattr(r, "routes", None)
    if routes_attr:
        print(f"    nested_routes_count={len(routes_attr)}")
        for j, nr in enumerate(routes_attr[:20], 1):
            ncls = type(nr).__name__
            npath = getattr(nr, "path", None)
            nname = getattr(nr, "name", None)
            nmethods = getattr(nr, "methods", None)
            nendpoint = getattr(nr, "endpoint", None)
            nendpoint_name = getattr(nendpoint, "__name__", None) if nendpoint else None
            print(f"      - [{j}] CLASS={ncls} path={npath!r} methods={sorted(nmethods) if nmethods else None} name={nname!r} endpoint={nendpoint_name!r}")
    print()

print("=== MOUNTED/ SKIPPED ===")
print("mounted_routers =", getattr(app.state, "mounted_routers", None))
print("skipped_routers =", getattr(app.state, "skipped_routers", None))
PYEOF

echo
echo "REPORT: $REPORT"
echo "=== KONIEC INSPECT ROUTE OBJECTS ==="
