#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "1. DIAGNOSTIKA BACKENDU"
echo "=========================================="
tail -50 ~/cmep-backend.log 2>&1 || echo "Log neexistuje"

echo ""
echo "=========================================="
echo "2. KONTROLA BEZIACICH PROCESOV"
echo "=========================================="
ps aux | grep -E "uvicorn|python.*app|node|next" | grep -v grep || echo "Ziadne procesy nebezia"

echo ""
echo "=========================================="
echo "3. SPUSTENIE BACKENDU (AK NEBEZI)"
echo "=========================================="
cd ~/waste-platform

# Skontroluj ci backend uz bezi
if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "Spustam backend..."
    # Aktivacia venv ak existuje
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    # Spustenie backendu
    nohup uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload > ~/cmep-backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend spusteny s PID: $BACKEND_PID"
    sleep 3
else
    echo "Backend uz bezi"
fi

echo ""
echo "=========================================="
echo "4. KONTROLA BACKENDU"
echo "=========================================="
curl -s -o /dev/null -w "Backend HTTP status: %{http_code}\n" http://localhost:8001/health 2>&1 || echo "Backend neodpoveda"

echo ""
echo "=========================================="
echo "5. SPUSTENIE FRONTENDU (AK NEBEZI)"
echo "=========================================="
if ! pgrep -f "next dev" > /dev/null; then
    echo "Spustam frontend..."
    cd ~/waste-platform/apps/web
    nohup npm run dev > ~/cmep-frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend spusteny s PID: $FRONTEND_PID"
    sleep 5
else
    echo "Frontend uz bezi"
fi

echo ""
echo "=========================================="
echo "6. KONTROLA FRONTENDU"
echo "=========================================="
curl -s -o /dev/null -w "Frontend HTTP status: %{http_code}\n" http://localhost:3001 2>&1 || echo "Frontend neodpoveda"

echo ""
echo "=========================================="
echo "7. STATUS SLUZIEB"
echo "=========================================="
echo "--- Beziace procesy ---"
ps aux | grep -E "uvicorn|next" | grep -v grep || echo "Ziadne"

echo ""
echo "=========================================="
echo "8. GIT STAV (OPRAVENE PRÍKAZY)"
echo "=========================================="
cd ~/waste-platform
echo "Zmenene subory:"
git status --short | wc -l
echo ""
echo "Posledne commity:"
git log --oneline -3
echo ""
echo "Aktualna vetva:"
git branch --show-current

echo ""
echo "=========================================="
echo "9. POKUS O COMMIT (AK SU ZMENY)"
echo "=========================================="
if [ -n "$(git status --short)" ]; then
    echo "Nachadzam zmeny, commitnem..."
    git add README.md app/core/config.py apps/web/src/lib/config.ts 2>/dev/null || echo "Niektore subory neexistuju"
    git commit -m "fix: update config and readme - $(date +%Y%m%d-%H%M)" 2>&1 || echo "Ziadne zmeny na commitu"
else
    echo "Ziadne zmeny na commitu"
fi

echo ""
echo "=========================================="
echo "10. SSH KONTROLA (BEZ SKUTOCNEHO PRIJONENIA)"
echo "=========================================="
which ssh && ssh -V
echo ""
echo "SSH kluc:"
ls -la ~/.ssh/id_* 2>/dev/null || echo "Ziadne SSH kluce"

echo ""
echo "=========================================="
echo "11. SIETOVE ROZHRANIA PRE VPS"
echo "=========================================="
ip addr show 2>/dev/null | grep -E "inet " | grep -v 127.0.0.1 || ifconfig 2>/dev/null | grep -E "inet " | grep -v 127.0.0.1 || echo "Nepodarilo sa zistit IP adresy"

echo ""
echo "=========================================="
echo "HOTOVO - Kompletna diagnostika a opravy"
echo "=========================================="
