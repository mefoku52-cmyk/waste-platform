#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "=== Spúšťam backend ==="

# Zabijeme starý proces
pkill -f "uvicorn app.main:app" 2>/dev/null || true

cd backend

# Aktivácia venv
source venv/bin/activate || source venv/Scripts/activate || true

# Spustenie v pozadí
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &

# Čakanie na spustenie
sleep 5

echo ""
echo "=== Testovanie endpointov ==="

# Health check
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health endpoint: OK"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "  (json output)"
else
    echo "❌ Health endpoint: FAILED"
    echo "Posledné logy:"
    tail -n 30 logs/backend.log 2>/dev/null || echo "  (žiadne logy)"
fi

echo ""
# Docs
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Docs endpoint: OK (HTTP $HTTP_CODE)"
else
    echo "❌ Docs endpoint: FAILED (HTTP $HTTP_CODE)"
fi

echo ""
echo "=== Backend beží ==="
echo "URL: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"

cd ..
