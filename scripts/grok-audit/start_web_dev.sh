#!/usr/bin/env bash
set -eu
cd "$HOME/waste-platform/apps/web"

echo "===== WEB DEV ====="
echo "PWD=$(pwd)"
echo "NODE=$(command -v node || true)"
echo "NPM=$(command -v npm || true)"
node -v 2>/dev/null || { echo "CHYBA: node nie je v PATH"; exit 1; }

if [ ! -d node_modules ]; then
  echo "===== npm ci ====="
  npm ci
fi

echo "===== start http://127.0.0.1:3001 ====="
echo "Dashboard: http://127.0.0.1:3001/dashboard"
echo "Login:     http://127.0.0.1:3001/login"
exec npm run dev
