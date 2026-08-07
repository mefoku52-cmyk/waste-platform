#!/bin/bash
set -e

echo "=== 1. Nastavenie PGDATA ==="
export PGDATA=$PREFIX/var/lib/postgresql
mkdir -p $PGDATA

echo "=== 2. Inicializácia databázy (ak neexistuje) ==="
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    initdb $PGDATA
else
    echo "Databáza už bola inicializovaná."
fi

echo "=== 3. Spustenie PostgreSQL servera ==="
if ! pg_ctl -D $PGDATA status > /dev/null 2>&1; then
    pg_ctl -D $PGDATA -l logfile start
else
    echo "PostgreSQL už beží."
fi

echo "=== 4. Vytvorenie používateľa a databázy ==="
createuser -s recyclehub 2>/dev/null || true
createdb -O recyclehub recyclehub 2>/dev/null || true
psql -d recyclehub -c "ALTER USER recyclehub WITH PASSWORD 'recyclehub';" 2>/dev/null || true

echo "=== 5. Spustenie Alembic migrácií ==="
alembic upgrade head

echo "=== Hotovo! Databáza je pripravená. ==="
