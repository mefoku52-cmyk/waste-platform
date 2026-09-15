#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

echo "=== 1. Kill starych procesov ==="
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "[x] uvicorn" || echo "[i] uvicorn nebezi"
pkill -f "next dev" 2>/dev/null && echo "[x] next dev" || echo "[i] next dev nebezi"
pkill -f "next-server" 2>/dev/null && echo "[x] next-server" || echo "[i] next-server nebezi"
sleep 2

echo
echo "=== 2. Postgres ==="
sv up postgres 2>/dev/null
sleep 3
sv status postgres | head -1

echo
echo "=== 3. Redis ==="
if redis-cli ping >/dev/null 2>&1; then
  echo "[ok] Redis bezi"
else
  redis-server --daemonize yes --port 6379
  sleep 2
  redis-cli ping
fi

echo
echo "=== 4. Backend (port 8001) ==="
mkdir -p logs
nohup make dev > logs/backend.log 2>&1 &
echo "[i] Backend spusteny na pozadi (log: logs/backend.log)"

echo
echo "=== 5. Frontend (port 3001) ==="
cd apps/web
nohup npm run dev > ../../logs/frontend.log 2>&1 &
echo "[i] Frontend spusteny na pozadi (log: logs/frontend.log)"
cd ..

echo
echo "=== 6. Cakam 10 sekund na start ==="
sleep 10

echo
echo "=== 7. Kontrola ==="
echo -n "Postgres:  "; pgrep -f "postgres -D" >/dev/null && echo "OK" || echo "CHYBA"
echo -n "Redis:     "; redis-cli ping 2>/dev/null || echo "CHYBA"
echo -n "Backend:   "; curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8001/health 2>/dev/null || echo "CHYBA"
echo -n "Frontend:  "; curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3001 2>/dev/null || echo "CHYBA"

echo
echo "=== 8. Uzitocne ==="
echo "Frontend: http://127.0.0.1:3001"
echo "Backend:  http://127.0.0.1:8001/docs"
echo "Logy:"
echo "  tail -f ~/waste-platform/logs/backend.log"
echo "  tail -f ~/waste-platform/logs/frontend.log"
echo
echo "Zastavit vsetko:"
echo "  pkill -f 'uvicorn app.main:app'"
echo "  pkill -f 'next dev'"
echo "  redis-cli shutdown"
