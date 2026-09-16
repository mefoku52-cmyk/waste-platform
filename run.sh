#!/usr/bin/env bash
cd ~/waste-platform

echo "=== 1. Kill starych procesov ==="
pkill -9 -f "uvicorn app.main:app" 2>/dev/null
pkill -9 -f "next dev" 2>/dev/null
pkill -9 -f "next-server" 2>/dev/null
sleep 2

echo "=== 2. Postgres ==="
sv up postgres 2>/dev/null
sleep 3

echo "=== 3. Redis ==="
redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes --port 6379
sleep 1
redis-cli ping

echo "=== 4. Backend (8001) ==="
mkdir -p logs
nohup make dev > logs/backend.log 2>&1 &

echo "=== 5. Frontend (3001) ==="
cd apps/web
nohup npm run dev > ../../logs/frontend.log 2>&1 &
cd ../..

echo "=== 6. Cakam 10s ==="
sleep 10

echo "=== 7. Stav ==="
echo -n "Postgres:  "; pgrep -f "postgres -D" >/dev/null && echo "OK" || echo "CHYBA"
echo -n "Redis:     "; redis-cli ping 2>/dev/null || echo "CHYBA"
echo -n "Backend:   "; curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8001/health 2>/dev/null || echo "CHYBA"
echo -n "Frontend:  "; curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3001 2>/dev/null || echo "CHYBA"

echo
echo "Otvori: http://127.0.0.1:3001"
