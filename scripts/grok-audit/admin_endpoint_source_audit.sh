#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/admin_endpoint_source_audit_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== ADMIN ENDPOINT SOURCE AUDIT ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

echo "## 1. SEARCH EXACT STRINGS"
grep -RniE "/admin/stats|/admin/users" "$PROJECT/app" "$PROJECT/apps/web/src" 2>/dev/null || true
echo

echo "## 2. SEARCH ADMIN ROUTERS"
find "$PROJECT/app" -type f | grep -E '/admin/.*/router\.py$|/admin/.*router\.py$|/presentation/router\.py$' | sort
echo

echo "## 3. SEARCH APIRouter PREFIXES WITH ADMIN"
grep -RniE 'APIRouter\(prefix="/admin|prefix=.*/admin' "$PROJECT/app" 2>/dev/null || true
echo

echo "## 4. SEARCH FUNCTIONS THAT LOOK LIKE STATS/USERS FOR ADMIN PAGE"
grep -RniE 'stats|total_users|total_listings|total_companies|pending_verifications|list_users|PaginatedUsersResponse' "$PROJECT/app" 2>/dev/null | head -n 300 || true
echo

echo "## 5. READ USERS ROUTER"
if [ -f "$PROJECT/app/modules/users/presentation/router.py" ]; then
  nl -ba "$PROJECT/app/modules/users/presentation/router.py" | sed -n '1,260p'
else
  echo "[INFO] Missing users router"
fi
echo

echo "## 6. READ ADMIN ROUTER"
if [ -f "$PROJECT/app/modules/admin/presentation/router.py" ]; then
  nl -ba "$PROJECT/app/modules/admin/presentation/router.py" | sed -n '1,260p'
else
  echo "[INFO] Missing admin router"
fi
echo

echo "## 7. READ ADMIN DASHBOARD PAGE"
if [ -f "$PROJECT/apps/web/src/app/dashboard/admin/page.tsx" ]; then
  nl -ba "$PROJECT/apps/web/src/app/dashboard/admin/page.tsx" | sed -n '1,260p'
else
  echo "[INFO] Missing admin dashboard page"
fi
echo

echo "## 8. READ FRONTEND ADMIN API"
if [ -f "$PROJECT/apps/web/src/features/admin/api.ts" ]; then
  nl -ba "$PROJECT/apps/web/src/features/admin/api.ts" | sed -n '1,220p'
else
  echo "[INFO] Missing frontend admin api"
fi
echo

echo "REPORT: $REPORT"
echo "=== KONIEC ADMIN ENDPOINT SOURCE AUDIT ==="
