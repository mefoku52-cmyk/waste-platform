#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "ČISTÝ REŠTART VŠETKÝCH SLUŽIEB"
echo "=========================================="

echo ""
echo "1. ZISTENIE BEŽIACICH PROCESOV"
echo "=========================================="
echo "--- Bežiace procesy pred zastavením ---"
ps aux | grep -E "uvicorn|next|postgres|redis" | grep -v grep || echo "Žiadne procesy nebežia"

echo ""
echo "2. ZASTAVENIE VŠETKÝCH SLUŽIEB"
echo "=========================================="

# Zastavenie backendu (uvicorn)
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "Zastavujem backend (uvicorn)..."
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    sleep 1
    echo "✓ Backend zastavený"
else
    echo "ℹ Backend už nebeží"
fi

# Zastavenie frontendu (next)
if pgrep -f "next dev" > /dev/null; then
    echo "Zastavujem frontend (next)..."
    pkill -f "next" 2>/dev/null || true
    sleep 1
    echo "✓ Frontend zastavený"
else
    echo "ℹ Frontend už nebeží"
fi

# Zastavenie PostgreSQL
if pgrep -f "postgres" > /dev/null; then
    echo "Zastavujem PostgreSQL..."
    pg_ctl -D ~/waste-platform/var/postgres stop 2>/dev/null || true
    sleep 1
    echo "✓ PostgreSQL zastavený"
else
    echo "ℹ PostgreSQL už nebeží"
fi

# Zastavenie Redis
if pgrep -f "redis" > /dev/null; then
    echo "Zastavujem Redis..."
    pkill -f "redis" 2>/dev/null || true
    sleep 1
    echo "✓ Redis zastavený"
else
    echo "ℹ Redis už nebeží"
fi

echo ""
echo "3. KONTROLA PO ZASTAVENÍ"
echo "=========================================="
ps aux | grep -E "uvicorn|next|postgres|redis" | grep -v grep || echo "✓ Všetky služby zastavené"

echo ""
echo "4. SPUSTENIE POSTGRESQL"
echo "=========================================="
cd ~/waste-platform
if [ -d "var/postgres" ]; then
    echo "Spúšťam PostgreSQL..."
    pg_ctl -D ~/waste-platform/var/postgres start -l ~/postgres.log 2>&1
    sleep 2
    echo "✓ PostgreSQL spustený"
else
    echo "ℹ PostgreSQL adresár neexistuje (preskakujem)"
fi

echo ""
echo "5. SPUSTENIE BACKENDU"
echo "=========================================="
echo "Spúšťam backend na porte 8001..."
cd ~/waste-platform
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > ~/cmep-backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend spustený s PID: $BACKEND_PID"
sleep 3

echo ""
echo "6. SPUSTENIE FRONTENDU"
echo "=========================================="
echo "Spúšťam frontend na porte 3001..."
cd ~/waste-platform/apps/web
nohup npm run dev -- --hostname 0.0.0.0 --port 3001 > ~/cmep-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend spustený s PID: $FRONTEND_PID"
sleep 5

echo ""
echo "7. KONTROLA STAVU"
echo "=========================================="

# Kontrola backendu
echo -n "Backend (http://localhost:8001/health): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health | grep -q "200"; then
    echo "✅ OK (HTTP 200)"
else
    echo "❌ FAIL"
    echo "   Skontroluj log: tail -20 ~/cmep-backend.log"
fi

# Kontrola frontendu
echo -n "Frontend (http://localhost:3001): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 | grep -q "200"; then
    echo "✅ OK (HTTP 200)"
else
    echo "❌ FAIL"
    echo "   Skontroluj log: tail -20 ~/cmep-frontend.log"
fi

# Kontrola PostgreSQL
echo -n "PostgreSQL (localhost:5432): "
if pgrep -f "postgres" > /dev/null; then
    echo "✅ OK (beží)"
else
    echo "❌ FAIL (nebeží)"
fi

echo ""
echo "8. ZHRNUTIE"
echo "=========================================="
echo "✅ Backend:  http://localhost:8001"
echo "✅ Frontend: http://localhost:3001"
echo "✅ API Docs: http://localhost:8001/docs"
echo ""
echo "📋 Logy:"
echo "   Backend:  tail -f ~/cmep-backend.log"
echo "   Frontend: tail -f ~/cmep-frontend.log"
echo "   Postgres: tail -f ~/postgres.log"
echo ""
echo "🛑 Zastavenie: pkill -f uvicorn && pkill -f next"
echo ""
echo "=========================================="
echo "HOTOVO - VŠETKO BEŽÍ NAČISTO!"
echo "=========================================="
