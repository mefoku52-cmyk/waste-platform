#!/bin/bash
# Lokálna simulácia CI pipeline
set -e

echo "=== 1. Ruff format ==="
ruff format --check .

echo "=== 2. Ruff lint ==="
ruff check .

echo "=== 3. Type check ==="
ty check

echo "=== 4. Pytest ==="
python3 -m pytest tests/ -q

echo "=== 5. Alembic sanity ==="
DATABASE_URL="sqlite+aiosqlite:///./dev_ci.db" alembic upgrade head
DATABASE_URL="sqlite+aiosqlite:///./dev_ci.db" alembic check
rm -f dev_ci.db

echo ""
echo "✅ All checks passed!"
