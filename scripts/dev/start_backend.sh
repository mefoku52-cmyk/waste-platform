#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

cd backend

# Aktivácia venv
source venv/bin/activate || source venv/Scripts/activate || true

# Spustenie v pozadí
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &

# Čakanie na spustenie
sleep 5

# Kontrola endpointov
echo "Kontrola endpointov..."

# Health check
curl -s http://localhost:8000/health || echo "Health endpoint nefunguje"

# OpenAPI
curl -s http://localhost:8000/openapi.json | head -c 200 || echo "OpenAPI endpoint nefunguje"

# Docs
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs || echo "Docs endpoint nefunguje"

echo "Backend spustený na http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
cd ..
