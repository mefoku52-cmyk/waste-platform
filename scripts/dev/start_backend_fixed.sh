#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

cd backend

# Aktivácia venv
source venv/bin/activate || source venv/Scripts/activate || true

# Zabezpečenie logs adresára
mkdir -p logs

# Spustenie v pozadí
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &

# Čakanie na spustenie
sleep 8

# Kontrola endpointov
echo "Kontrola endpointov..."

# Health check
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Health endpoint funguje"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "❌ Health endpoint nefunguje"
    echo "Posledné logy:"
    tail -n 20 logs/backend.log
fi

# OpenAPI
if curl -s http://localhost:8000/openapi.json > /dev/null; then
    echo "✅ OpenAPI endpoint funguje"
else
    echo "❌ OpenAPI endpoint nefunguje"
fi

# Docs
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Docs endpoint funguje (HTTP $HTTP_CODE)"
else
    echo "❌ Docs endpoint nefunguje (HTTP $HTTP_CODE)"
fi

echo ""
echo "Backend spustený na http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
echo "OpenAPI: http://localhost:8000/openapi.json"
echo ""
echo "Logy: tail -f backend/logs/backend.log"

cd ..
