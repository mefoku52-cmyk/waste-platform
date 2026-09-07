#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
WEB="$PROJECT/apps/web"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/run_web_typecheck_and_build_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== RUN WEB TYPECHECK AND BUILD ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo "WEB: $WEB"
echo

cd "$WEB"

echo "## PACKAGE FILE"
nl -ba "$WEB/package.json" | sed -n '1,220p'
echo

echo "## NODE / NPM"
command -v node || true
node --version || true
command -v npm || true
npm --version || true
echo

echo "## INSTALLED NODE_MODULES CHECK"
if [ -d "$WEB/node_modules" ]; then
  echo "[OK] node_modules exists: $WEB/node_modules"
else
  echo "[CHYBA] Missing node_modules: $WEB/node_modules"
fi
echo

echo "## TYPECHECK"
npm run typecheck
echo

echo "## BUILD"
npm run build
echo

echo "REPORT: $REPORT"
echo "=== KONIEC RUN WEB TYPECHECK AND BUILD ==="
