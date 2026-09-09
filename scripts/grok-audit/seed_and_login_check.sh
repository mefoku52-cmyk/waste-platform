#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Aktualna DB konfiguracia backendu ==="
curl -s http://localhost:8001/health || true
echo

echo ""
echo "=== 2. Seed databazy cez oficialny projektovy skript ==="
python3 scripts/ops/seed_database.py
SEED_EXIT=$?
echo "seed exit code: $SEED_EXIT"

echo ""
echo "=== 3. Overenie admina v SQLite ==="
python3 <<'PY'
import sqlite3

con = sqlite3.connect("var/cmep.db")
row = con.execute(
    "SELECT id, email, status, first_name, last_name "
    "FROM users WHERE email = ?",
    ("admin@cmep.dev",),
).fetchone()

if row:
    print("Admin existuje:")
    print(f"id={row[0]}")
    print(f"email={row[1]}")
    print(f"status={row[2]}")
    print(f"meno={row[3]} {row[4]}")
else:
    print("CHYBA: admin@cmep.dev sa nenasiel")
con.close()
PY

echo ""
echo "=== 4. Login test ==="
LOGIN_RESPONSE="$(curl -sS -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@cmep.dev","password":"Admin123!"}')"
printf '%s
' "$LOGIN_RESPONSE"

echo ""
echo "=== 5. Overenie accessToken kluca bez vypisania tokenu ==="
printf '%s' "$LOGIN_RESPONSE" | python3 - <<'PY'
import json
import sys

try:
    payload = json.load(sys.stdin)
except json.JSONDecodeError as exc:
    print(f"CHYBA: odpoved nie je JSON: {exc}")
    raise SystemExit(1)

if "accessToken" in payload:
    print("OK: login vratil accessToken")
    print("tokenType:", payload.get("tokenType"))
    print("expiresIn:", payload.get("expiresIn"))
else:
    print("LOGIN ZLYHAL:", payload)
    raise SystemExit(1)
PY
