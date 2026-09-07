#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/check_backend_runtime_mount_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== CHECK BACKEND RUNTIME MOUNT ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

echo "=== 1. PYTHON KONTEXT ==="
python3 -c 'import sys; print("PYTHON:", sys.executable); print("PREFIX:", sys.prefix)'
echo

echo "=== 2. IMPORT app.main ==="
python3 - <<'PYEOF'
import traceback
try:
    import app.main as main_mod
    print("[IMPORT OK] app.main")
    print("app objekt:", hasattr(main_mod, "app"))
    print("create_app objekt:", hasattr(main_mod, "create_app"))
except Exception as e:
    print("[IMPORT FAIL] app.main")
    print(repr(e))
    traceback.print_exc()
PYEOF
echo

echo "=== 3. CREATE_APP A STAV ROUTEROV ==="
python3 - <<'PYEOF'
import traceback
try:
    from app.main import create_app
    app = create_app()
    mounted = getattr(app.state, "mounted_routers", None)
    skipped = getattr(app.state, "skipped_routers", None)
    print("[CREATE_APP OK]")
    print("mounted_routers =", mounted)
    print("skipped_routers =", skipped)
    print("routes_count =", len(getattr(app, "routes", [])))
    print("routes_sample =")
    for r in getattr(app, "routes", [])[:80]:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None)
        print(" -", path, methods)
except Exception as e:
    print("[CREATE_APP FAIL]")
    print(repr(e))
    traceback.print_exc()
PYEOF
echo

echo "=== 4. PRIAME IMPORTY MODULOVYCH ROUTEROV ==="
python3 - <<'PYEOF'
import importlib

modules = [
    "app.shared.presentation.api_router",
    "app.modules.auth.presentation.router",
    "app.modules.users.presentation.router",
    "app.modules.companies.presentation.router",
    "app.modules.company_memberships.presentation.router",
    "app.modules.listings.presentation.router",
    "app.modules.inquiries.presentation.router",
    "app.modules.documents.presentation.router",
    "app.modules.compliance.presentation.router",
    "app.modules.notifications.presentation.router",
    "app.modules.analytics.presentation.router",
    "app.modules.admin.presentation.router",
    "app.modules.uploads.presentation.router",
]

for mod_path in modules:
    try:
        mod = importlib.import_module(mod_path)
        router = getattr(mod, "router", None)
        if router is None:
            print(f"[WARN] {mod_path} -> router attribute missing")
        else:
            print(f"[OK] {mod_path} -> router loaded")
    except Exception as e:
        print(f"[FAIL] {mod_path} -> {repr(e)}")
PYEOF
echo

echo "=== 5. HEALTH ENDPOINT SIGNAL ==="
grep -RniE '@app\.get\("/health"\)|@router\.get\("/health"\)' "$PROJECT/app" --include='*.py' 2>/dev/null || true
echo

echo "REPORT: $REPORT"
echo "=== KONIEC CHECK BACKEND RUNTIME MOUNT ==="
