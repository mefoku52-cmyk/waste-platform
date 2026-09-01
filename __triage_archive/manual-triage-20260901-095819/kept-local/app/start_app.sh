#!/bin/bash

echo "🚀 SPÚŠŤAM CMEP PLATFORM"
echo "========================================="

# 1. Zabi staré procesy
echo ""
echo "📋 Zastavujem staré procesy..."
pkill -f uvicorn 2>/dev/null
pkill -f "python.*main" 2>/dev/null
sleep 2

# 2. Nastav prostredie
echo ""
echo "📋 Nastavujem prostredie..."
cd ~/waste-platform
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# 3. Aktivuj virtuálne prostredie (ak existuje)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 4. Spusti aplikáciu
echo ""
echo "📋 Spúšťam aplikáciu na porte 8000..."
cd app
uvicorn main:app --reload --port 8000 --host 0.0.0.0

