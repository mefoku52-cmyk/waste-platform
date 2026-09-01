#!/bin/bash

echo "🔧 OPRAVA SPUSTENIA APLIKÁCIE"
echo "========================================="

# 1. Choď do koreňa
cd ~/waste-platform
echo "📋 1. Adresár: $(pwd)"

# 2. Nastav PYTHONPATH
echo ""
echo "📋 2. Nastavujem PYTHONPATH..."
export PYTHONPATH="${PYTHONPATH}:${PWD}"
echo "✅ PYTHONPATH: $PYTHONPATH"

# 3. Zabi staré procesy
echo ""
echo "📋 3. Zastavujem staré procesy..."
pkill -f uvicorn 2>/dev/null
sleep 2

# 4. Spusti aplikáciu z koreňa
echo ""
echo "📋 4. Spúšťam aplikáciu..."
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 &

# 5. Počkaj a otestuj
sleep 5
echo ""
echo "📋 5. Test API..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ Aplikácia neodpovedá"

# 6. Zhrnutie
echo ""
echo "========================================="
echo "📊 ZHRNUTIE"
echo "========================================="
echo "✅ Aplikácia: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null)"
echo "🔗 http://localhost:8000/docs"
echo "========================================="
