#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Health check ==="
curl -s http://localhost:8001/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'DB: {d["database_url"]}')"

echo ""
echo "=== 2. Login s bootstrap adminom ==="
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cmep-bootstrap.dev","password":"password"}' 2>&1 | python3 -m json.tool

echo ""
echo "=== 3. Login s tvojim emailom ==="
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mefoku52@gmail.com","password":"password"}' 2>&1 | python3 -m json.tool

echo ""
echo "=== 4. Skus ine hesla ==="
for pwd in "password" "Admin123!" "changeit" "test"; do
    echo "--- Heslo: $pwd ---"
    curl -s -X POST http://localhost:8001/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d "{"email":"admin@cmep-bootstrap.dev","password":"$pwd"}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'accessToken' in d else f'FAIL: {d.get("detail",d)[:50]}')"
done
