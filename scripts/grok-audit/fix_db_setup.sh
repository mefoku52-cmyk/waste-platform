#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Kontrola SQLite DB (ci existuju tabulky) ==="
ls -la var/cmep.db 2>/dev/null || echo "SQLite DB neexistuje"

echo ""
echo "=== 2. Zoznam tabuliek v SQLite ==="
if [ -f var/cmep.db ]; then
    sqlite3 var/cmep.db ".tables" | head -30
fi

echo ""
echo "=== 3. Vytvorenie SQL dump zo SQLite ==="
if [ -f var/cmep.db ]; then
    sqlite3 var/cmep.db ".dump" > /tmp/cmep_sqlite_dump.sql 2>&1
    wc -l /tmp/cmep_sqlite_dump.sql
    head -50 /tmp/cmep_sqlite_dump.sql
fi

echo ""
echo "=== 4. Migracne verzie ==="
ls -la migrations/versions/ | head -20

echo ""
echo "=== 5. Prva migracia (initial schema) ==="
head -100 migrations/versions/*_initial*.py 2>/dev/null | head -80
