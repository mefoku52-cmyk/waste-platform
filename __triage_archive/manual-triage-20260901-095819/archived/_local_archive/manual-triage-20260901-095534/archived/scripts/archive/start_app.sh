#!/bin/bash
set -e
cd /data/data/com.termux/files/home/waste-platform

echo "[1/3] Loading environment..."
export $(grep -v '^#' .env | xargs)

echo "[2/3] Starting BACKEND on :8001 ..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1 &
BACKEND_PID=$!

echo "[3/3] Starting FRONTEND on :3001 ..."
cd apps/web
npm run dev -- -p 3001 &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  BACKEND:  http://localhost:8001"
echo "  FRONTEND: http://localhost:3001"
echo "=========================================="
echo ""
echo "Stop: kill $BACKEND_PID $FRONTEND_PID"
wait
