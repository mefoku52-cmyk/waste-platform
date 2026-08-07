#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

cd backend

# Aktivácia venv
source venv/bin/activate || source venv/Scripts/activate || true

# Nastavenie PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"

echo "=== Vytváram migrácie ==="
alembic revision --autogenerate -m "Add all models"

echo ""
echo "=== Spúšťam migrácie ==="
alembic upgrade head

echo ""
echo "✅ Migrácie úspešne vykonané"

cd ..
