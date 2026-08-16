#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/waste-platform"
cd "$ROOT"

echo "=== CMEP start ==="

# Postgres
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
  echo "[pg] starting..."
  pg_ctl -D "$PREFIX/var/lib/postgresql" start || true
  sleep 2
fi
pg_isready -h localhost -p 5432 && echo "[pg] ok" || echo "[pg] FAIL"

# Redis
if ! redis-cli ping 2>/dev/null | grep -q PONG; then
  echo "[redis] starting..."
  redis-server --daemonize yes || true
  sleep 1
fi
redis-cli ping 2>/dev/null | grep -q PONG && echo "[redis] ok" || echo "[redis] FAIL"

# stop old
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 1

# backend
echo "[backend] :8001"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload \
  > "$HOME/cmep-backend.log" 2>&1 &
echo "backend pid $!"

# frontend
echo "[frontend] :3001"
cd "$ROOT/apps/web"
nohup npm run dev -- --port 3001 --hostname 0.0.0.0 \
  > "$HOME/cmep-frontend.log" 2>&1 &
echo "frontend pid $!"

sleep 6
curl -s -m 5 http://localhost:8001/health || echo "backend not ready"
echo ""
curl -s -m 5 -o /dev/null -w "frontend HTTP %{http_code}\n" http://localhost:3001 || echo "frontend not ready"

echo ""
echo "API:  http://localhost:8001/docs"
echo "WEB:  http://localhost:3001"
echo "Logs: tail -f ~/cmep-backend.log ~/cmep-frontend.log"
