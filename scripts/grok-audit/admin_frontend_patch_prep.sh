#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/admin_frontend_patch_prep_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== ADMIN FRONTEND PATCH PREP ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

FILES="
$PROJECT/apps/web/src/features/admin/api.ts
$PROJECT/apps/web/src/features/admin/hooks/use-admin-stats.ts
$PROJECT/apps/web/src/features/admin/hooks/use-admin-users.ts
$PROJECT/apps/web/src/features/admin/components/admin-users-table.tsx
$PROJECT/apps/web/src/features/admin/index.ts
$PROJECT/apps/web/src/features/admin/types.ts
$PROJECT/apps/web/src/app/dashboard/admin/page.tsx
$PROJECT/apps/web/src/lib/api/http.ts
$PROJECT/apps/web/src/features/auth/index.ts
"

for f in $FILES; do
  echo "############################################################"
  echo "FILE: $f"
  echo "############################################################"
  if [ -f "$f" ]; then
    nl -ba "$f" | sed -n '1,260p'
  else
    echo "[INFO] Missing file"
  fi
  echo
done

echo "## SEARCH USER TYPES / RESPONSE SHAPES IN FRONTEND"
grep -RniE "UserData|PaginatedUsers|first_name|firstName|last_name|lastName|is_active|isActive|role|email" \
  "$PROJECT/apps/web/src" 2>/dev/null | head -n 300 || true
echo

echo "REPORT: $REPORT"
echo "=== KONIEC ADMIN FRONTEND PATCH PREP ==="
