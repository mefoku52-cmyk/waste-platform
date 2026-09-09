#!/usr/bin/env bash
set -u

cd ~/waste-platform
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "=== 1. Aktivna DB backendu ==="
curl -sS http://localhost:8001/health
echo

echo ""
echo "=== 2. Seed cez oficialny modul projektu ==="
python3 -m scripts.ops.seed_database
SEED_EXIT=$?
echo "seed exit code: $SEED_EXIT"

echo ""
echo "=== 3. Overenie admina v SQLite ==="
python3 -c '
import sqlite3
con = sqlite3.connect("var/cmep.db")
row = con.execute(
    "SELECT id, email, status, first_name, last_name FROM users WHERE email = ?",
    ("admin@cmep.dev",),
).fetchone()
print(row if row else "ADMIN_NOT_FOUND")
con.close()
'

echo ""
echo "=== 4. Login test ==="
curl -sS -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@cmep.dev","password":"Admin123!"}'
echo
