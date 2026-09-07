#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/p1_api_contract_check_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== P1 API CONTRACT CHECK ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

for DOMAIN in compliance notifications admin; do
  echo "############################################################"
  echo "### DOMAIN: $DOMAIN"
  echo "############################################################"
  echo

  ROUTER="$PROJECT/app/modules/$DOMAIN/presentation/router.py"
  FRONTEND_DIR="$PROJECT/apps/web/src/features/$DOMAIN"

  echo "## 1. BACKEND ROUTE SIGNALS"
  if [ -f "$ROUTER" ]; then
    grep -nE "@router\.(get|post|patch|delete)\(" "$ROUTER" || true
    echo
    nl -ba "$ROUTER" | grep -nE '"/|prefix=' || true
  else
    echo "[INFO] Missing router: $ROUTER"
  fi
  echo

  echo "## 2. FRONTEND ENDPOINT SIGNALS"
  if [ -d "$FRONTEND_DIR" ]; then
    grep -RniE "http\.(get|post|patch|delete)|fetch\(" "$FRONTEND_DIR" || true
    echo
    grep -RniE "'/compliance|'/notifications|'/admin|\"/compliance|\"/notifications|\"/admin" "$FRONTEND_DIR" || true
  else
    echo "[INFO] Missing frontend dir: $FRONTEND_DIR"
  fi
  echo

  echo "## 3. DOMAIN-SPECIFIC NOTES"
  if [ "$DOMAIN" = "compliance" ]; then
    echo "[EXPECT] Backend should expose list/get/create/update/delete."
    echo "[EXPECT] Frontend currently should be checked for missing get/update/delete usage."
  elif [ "$DOMAIN" = "notifications" ]; then
    echo "[EXPECT] Backend should expose list/get/create/mark-read/mark-unread/delete."
    echo "[EXPECT] Frontend currently should be checked for missing create/mark-read/mark-unread/delete usage."
  elif [ "$DOMAIN" = "admin" ]; then
    echo "[EXPECT] Frontend currently references /admin, /admin/stats, /admin/users."
    echo "[EXPECT] Backend router excerpt showed /admin, /admin/all, /admin/{id}, POST /admin."
    echo "[RISK] Possible contract mismatch for /admin/stats and /admin/users unless defined elsewhere."
  fi
  echo

  echo "## 4. CROSS-PROJECT SEARCH FOR SUSPICIOUS ENDPOINTS"
  if [ "$DOMAIN" = "admin" ]; then
    grep -RniE "/admin/stats|/admin/users|stats|users" "$PROJECT/app" "$PROJECT/apps/web/src" 2>/dev/null | head -n 200 || true
  elif [ "$DOMAIN" = "notifications" ]; then
    grep -RniE "mark-read|mark-unread|/notifications" "$PROJECT/app" "$PROJECT/apps/web/src" 2>/dev/null | head -n 200 || true
  else
    grep -RniE "/compliance|updateComplianceRecord|deleteComplianceRecord|getComplianceRecordById" "$PROJECT/app" "$PROJECT/apps/web/src" 2>/dev/null | head -n 200 || true
  fi
  echo
done

echo "REPORT: $REPORT"
echo "=== KONIEC P1 API CONTRACT CHECK ==="
