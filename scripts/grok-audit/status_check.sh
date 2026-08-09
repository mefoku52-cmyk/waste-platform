#!/usr/bin/env bash
echo "=========================================="
echo "  WASTE PLATFORM - STATUS CHECK"
echo "=========================================="

echo ""
echo "--- 1. Beží server? ---"
ps aux | grep "uvicorn app.main:app" | grep -v grep || echo "NEBEZI - treba spustit"

echo ""
echo "--- 2. Health check ---"
curl -s http://localhost:8001/health || echo "NEDOSTUPNY"

echo ""
echo ""
echo "--- 3. Kolko tabuliek/zaznamov je v DB ---"
python3 -c "
import sqlite3
conn = sqlite3.connect('waste_platform.db')
cur = conn.cursor()
cur.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
tables = sorted(r[0] for r in cur.fetchall())
print('Tabuliek:', len(tables), '-', tables)
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'  {t}: {cur.fetchone()[0]} zaznamov')
    except Exception as e:
        print(f'  {t}: chyba - {e}')
conn.close()
"

echo ""
echo "--- 4. Login test ---"
LOGIN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@cmep-bootstrap.dev", "password": "Bootstrap-Admin-2026!"}')
echo "$LOGIN" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Login: OK' if 'accessToken' in d else 'Login: ZLYHAL -', d)
except Exception as e:
    print('Login: CHYBA -', e)
"

echo ""
echo "--- 5. Pocet API ciest (OpenAPI schema) ---"
curl -s http://localhost:8001/openapi.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('API ciest:', len(d.get('paths', {})))
"

echo ""
echo "--- 6. Git stav (necommitnute zmeny?) ---"
git status --short | wc -l
echo "riadkov v git status (0 = vsetko commitnute)"

echo "=========================================="
