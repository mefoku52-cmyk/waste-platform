#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/check_web_build_commands_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== CHECK WEB BUILD COMMANDS ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

show_pkg() {
  local f="$1"
  echo "############################################################"
  echo "PACKAGE FILE: $f"
  echo "############################################################"
  if [ -f "$f" ]; then
    nl -ba "$f" | sed -n '1,240p'
  else
    echo "[INFO] Missing file"
  fi
  echo
}

show_pkg "$PROJECT/package.json"
show_pkg "$PROJECT/apps/web/package.json"
show_pkg "$PROJECT/pnpm-workspace.yaml"
show_pkg "$PROJECT/turbo.json"
show_pkg "$PROJECT/package-lock.json"
show_pkg "$PROJECT/pnpm-lock.yaml"
show_pkg "$PROJECT/yarn.lock"

echo "## NODE / PACKAGE MANAGERS"
command -v node || true
node --version || true
command -v npm || true
npm --version || true
command -v pnpm || true
pnpm --version || true
command -v yarn || true
yarn --version || true
echo

echo "## POSSIBLE SCRIPTS"
grep -RniE '\"(build|dev|lint|typecheck|check)\"[[:space:]]*:' \
  "$PROJECT/package.json" "$PROJECT/apps/web/package.json" 2>/dev/null || true
echo

echo "REPORT: $REPORT"
echo "=== KONIEC CHECK WEB BUILD COMMANDS ==="
