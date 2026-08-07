#!/data/data/com.termux/files/usr/bin/bash

set -e

cd backend

# Aktivácia venv
source venv/bin/activate || source venv/Scripts/activate || true

# Vytvorenie migrácií
echo "=== Vytváram migrácie ==="
alembic revision --autogenerate -m "Add all models" 2>/dev/null || echo "Migrácia už existuje"

echo ""
echo "=== Spúšťam migrácie ==="
alembic upgrade head

echo ""
echo "✅ Migrácie dokončené"

cd ..
