#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

echo "=== FÁZA 1 - Backend implementácia ==="
echo ""

# Aktivácia venv
cd backend
source venv/bin/activate || source venv/Scripts/activate || true

# Vytvorenie migrácií
echo "Vytváram migrácie..."
alembic revision --autogenerate -m "Add user, company, listing, reservation, membership, audit_log models"

# Spustenie migrácií
echo "Spúšťam migrácie..."
alembic upgrade head

cd ..

echo ""
echo "✅ Fáza 1 dokončená - modely vytvorené"
echo ""
echo "Ďalšie kroky:"
echo "1. Overiť backend: http://localhost:8000/docs"
echo "2. Pokračovať Fázou 2 - Frontend"
