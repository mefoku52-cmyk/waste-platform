#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/p1_triage_compliance_notifications_admin_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== P1 TRIAGE: COMPLIANCE + NOTIFICATIONS + ADMIN ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

for DOMAIN in compliance notifications admin; do
  echo "############################################################"
  echo "### DOMAIN: $DOMAIN"
  echo "############################################################"
  echo

  echo "## 1. BACKEND MODUL FILES"
  if [ -d "$PROJECT/app/modules/$DOMAIN" ]; then
    find "$PROJECT/app/modules/$DOMAIN" -type f | sort
  else
    echo "[CHYBA] Backend modul neexistuje: $PROJECT/app/modules/$DOMAIN"
  fi
  echo

  echo "## 2. BACKEND ROUTER SIGNALS"
  if [ -f "$PROJECT/app/modules/$DOMAIN/presentation/router.py" ]; then
    nl -ba "$PROJECT/app/modules/$DOMAIN/presentation/router.py" | sed -n '1,240p'
  else
    echo "[INFO] Router subor nenajdeny: $PROJECT/app/modules/$DOMAIN/presentation/router.py"
  fi
  echo

  echo "## 3. FRONTEND FEATURE FILES"
  if [ -d "$PROJECT/apps/web/src/features/$DOMAIN" ]; then
    find "$PROJECT/apps/web/src/features/$DOMAIN" -type f | sort
  else
    echo "[INFO] Frontend feature neexistuje: $PROJECT/apps/web/src/features/$DOMAIN"
  fi
  echo

  echo "## 4. FRONTEND API SIGNALS"
  if [ -d "$PROJECT/apps/web/src/features/$DOMAIN" ]; then
    grep -RniE "fetch\\(|http\\.|apiBaseUrl|/$DOMAIN|${DOMAIN%s}" "$PROJECT/apps/web/src/features/$DOMAIN" || true
  else
    echo "[INFO] Frontend grep preskoceny, feature neexistuje."
  fi
  echo

  echo "## 5. APP TEST SIGNALS"
  if [ -d "$PROJECT/app/tests" ]; then
    find "$PROJECT/app/tests" -type f | grep -i "$DOMAIN" || echo "[INFO] Ziadne app/tests signaly pre $DOMAIN"
  else
    echo "[INFO] Adresar neexistuje: $PROJECT/app/tests"
  fi
  echo

  echo "## 6. ROOT TEST SIGNALS"
  if [ -d "$PROJECT/tests" ]; then
    find "$PROJECT/tests" -type f | grep -i "$DOMAIN" || echo "[INFO] Ziadne root tests signaly pre $DOMAIN"
  else
    echo "[INFO] Adresar neexistuje: $PROJECT/tests"
  fi
  echo

  echo "## 7. CROSS-REFERENCE SIGNALS V CELOM PROJEKTE"
  grep -RniE "/api/v1/$DOMAIN|$DOMAIN" \
    "$PROJECT/app" \
    "$PROJECT/apps/web/src" \
    "$PROJECT/tests" 2>/dev/null | head -n 200 || true
  echo

  echo "## 8. QUICK CLASSIFICATION"
  backend="NO"
  frontend="NO"
  apptests="NO"
  roottests="NO"

  [ -d "$PROJECT/app/modules/$DOMAIN" ] && backend="YES"
  [ -d "$PROJECT/apps/web/src/features/$DOMAIN" ] && frontend="YES"
  find "$PROJECT/app/tests" -type f 2>/dev/null | grep -qi "$DOMAIN" && apptests="YES" || true
  find "$PROJECT/tests" -type f 2>/dev/null | grep -qi "$DOMAIN" && roottests="YES" || true

  echo "DOMAIN=$DOMAIN BACKEND=$backend FRONTEND=$frontend APP_TESTS=$apptests ROOT_TESTS=$roottests"

  if [ "$backend" = "YES" ] && [ "$frontend" = "YES" ] && [ "$apptests" = "NO" ] && [ "$roottests" = "NO" ]; then
    echo "CLASS=ui_backend_no_tests"
  elif [ "$backend" = "YES" ] && [ "$frontend" = "YES" ]; then
    echo "CLASS=partially_covered"
  elif [ "$backend" = "YES" ] && [ "$frontend" = "NO" ]; then
    echo "CLASS=backend_only_or_ui_missing"
  else
    echo "CLASS=unexpected_state"
  fi

  echo
done

echo "############################################################"
echo "### SUMMARY"
echo "############################################################"
echo "P1 DOMAINS: compliance, notifications, admin"
echo "REPORT: $REPORT"
echo "=== KONIEC P1 TRIAGE ==="
