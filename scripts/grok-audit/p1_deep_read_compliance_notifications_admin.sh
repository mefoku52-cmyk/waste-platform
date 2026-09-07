#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/p1_deep_read_compliance_notifications_admin_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== P1 DEEP READ: COMPLIANCE + NOTIFICATIONS + ADMIN ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

for DOMAIN in compliance notifications admin; do
  echo "############################################################"
  echo "### DOMAIN: $DOMAIN"
  echo "############################################################"
  echo

  echo "## A. BACKEND ROUTER (first 260 lines)"
  if [ -f "$PROJECT/app/modules/$DOMAIN/presentation/router.py" ]; then
    nl -ba "$PROJECT/app/modules/$DOMAIN/presentation/router.py" | sed -n '1,260p'
  else
    echo "[INFO] Missing backend router: $PROJECT/app/modules/$DOMAIN/presentation/router.py"
  fi
  echo

  echo "## B. FRONTEND API FILE"
  if [ -f "$PROJECT/apps/web/src/features/$DOMAIN/api.ts" ]; then
    nl -ba "$PROJECT/apps/web/src/features/$DOMAIN/api.ts" | sed -n '1,260p'
  else
    echo "[INFO] Missing frontend api file: $PROJECT/apps/web/src/features/$DOMAIN/api.ts"
  fi
  echo

  echo "## C. FRONTEND INDEX"
  if [ -f "$PROJECT/apps/web/src/features/$DOMAIN/index.ts" ]; then
    nl -ba "$PROJECT/apps/web/src/features/$DOMAIN/index.ts" | sed -n '1,220p'
  else
    echo "[INFO] Missing frontend index: $PROJECT/apps/web/src/features/$DOMAIN/index.ts"
  fi
  echo

  echo "## D. FRONTEND COMPONENTS"
  if [ -d "$PROJECT/apps/web/src/features/$DOMAIN/components" ]; then
    find "$PROJECT/apps/web/src/features/$DOMAIN/components" -type f | sort | while read -r f; do
      echo "----- FILE: $f -----"
      nl -ba "$f" | sed -n '1,220p'
      echo
    done
  else
    echo "[INFO] Missing components dir: $PROJECT/apps/web/src/features/$DOMAIN/components"
  fi
  echo

  echo "## E. FRONTEND HOOKS"
  if [ -d "$PROJECT/apps/web/src/features/$DOMAIN/hooks" ]; then
    find "$PROJECT/apps/web/src/features/$DOMAIN/hooks" -type f | sort | while read -r f; do
      echo "----- FILE: $f -----"
      nl -ba "$f" | sed -n '1,220p'
      echo
    done
  else
    echo "[INFO] Missing hooks dir: $PROJECT/apps/web/src/features/$DOMAIN/hooks"
  fi
  echo

  echo "## F. APP TEST FILE CANDIDATES"
  find "$PROJECT/app/tests" -type f 2>/dev/null | grep -i "$DOMAIN" || echo "[INFO] No app/tests files for $DOMAIN"
  echo

  echo "## G. ROOT TEST FILE CANDIDATES"
  find "$PROJECT/tests" -type f 2>/dev/null | grep -i "$DOMAIN" || echo "[INFO] No root tests files for $DOMAIN"
  echo

  echo "## H. QUICK GAP NOTE"
  backend_router="NO"
  frontend_api="NO"
  frontend_hooks="NO"
  frontend_components="NO"
  app_tests="NO"
  root_tests="NO"

  [ -f "$PROJECT/app/modules/$DOMAIN/presentation/router.py" ] && backend_router="YES"
  [ -f "$PROJECT/apps/web/src/features/$DOMAIN/api.ts" ] && frontend_api="YES"
  [ -d "$PROJECT/apps/web/src/features/$DOMAIN/hooks" ] && frontend_hooks="YES"
  [ -d "$PROJECT/apps/web/src/features/$DOMAIN/components" ] && frontend_components="YES"
  find "$PROJECT/app/tests" -type f 2>/dev/null | grep -qi "$DOMAIN" && app_tests="YES" || true
  find "$PROJECT/tests" -type f 2>/dev/null | grep -qi "$DOMAIN" && root_tests="YES" || true

  echo "DOMAIN=$DOMAIN BACKEND_ROUTER=$backend_router FRONTEND_API=$frontend_api FRONTEND_HOOKS=$frontend_hooks FRONTEND_COMPONENTS=$frontend_components APP_TESTS=$app_tests ROOT_TESTS=$root_tests"
  echo
done

echo "REPORT: $REPORT"
echo "=== KONIEC P1 DEEP READ ==="
