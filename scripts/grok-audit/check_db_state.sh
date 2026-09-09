#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== PostgreSQL databazy ==="
psql -U u0_a388 -h localhost -d postgres -c 'l'

echo ""
echo "=== Tabulky v cmep ==="
psql -U u0_a388 -h localhost -d cmep -c 'dt'

echo ""
echo "=== Migracne nastroje v projekte ==="
find . -maxdepth 3 -name 'alembic.ini' -print 2>/dev/null
find . -maxdepth 3 -name 'pyproject.toml' -print 2>/dev/null
find . -maxdepth 3 -name 'requirements*.txt' -print 2>/dev/null

echo ""
echo "=== Schema v DB (ak existuje) ==="
psql -U u0_a388 -h localhost -d cmep -c 'dn'

echo ""
echo "=== Existujuce tabulky (detailny zoznam) ==="
psql -U u0_a388 -h localhost -d cmep -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
