#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/domain_gap_matrix_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== DOMAIN GAP MATRIX ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

DOMAINS="auth users companies company_memberships listings inquiries documents compliance notifications analytics admin uploads"

echo "DOMAIN | BACKEND_MODULE | BACKEND_ROUTER | FRONTEND_FEATURE | APP_TESTS | ROOT_TESTS"
echo "------ | -------------- | -------------- | ---------------- | --------- | ----------"

for d in $DOMAINS; do
  backend_module="NO"
  backend_router="NO"
  frontend_feature="NO"
  app_tests="NO"
  root_tests="NO"

  if [ -d "$PROJECT/app/modules/$d" ]; then
    backend_module="YES"
  fi

  if [ -f "$PROJECT/app/modules/$d/presentation/router.py" ]; then
    backend_router="YES"
  fi

  if [ -d "$PROJECT/apps/web/src/features/$d" ]; then
    frontend_feature="YES"
  fi

  if find "$PROJECT/app/tests" -type f 2>/dev/null | grep -qi "$d"; then
    app_tests="YES"
  fi

  if find "$PROJECT/tests" -type f 2>/dev/null | grep -qi "$d"; then
    root_tests="YES"
  fi

  echo "$d | $backend_module | $backend_router | $frontend_feature | $app_tests | $root_tests"
done

echo
echo "REPORT: $REPORT"
echo "=== KONIEC DOMAIN GAP MATRIX ==="
