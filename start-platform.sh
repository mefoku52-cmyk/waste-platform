#!/data/data/com.termux/files/usr/bin/bash

echo "=== CMEP Platform Start ==="

# Backend
echo "[1/2] Spúšťam backend (port 8001)..."
cd ~/waste-platform
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

sleep 3

# Frontend
echo "[2/2] Spúšťam frontend (port 3001)..."
cd ~/waste-platform/apps/web
npm run dev -- --port 3001 --hostname 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://localhost:8001"
echo "Frontend: http://localhost:3001"
echo "API docs: http://localhost:8001/docs"
echo ""
echo "Na zastavenie stlač Ctrl+C"
echo "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"

wait
