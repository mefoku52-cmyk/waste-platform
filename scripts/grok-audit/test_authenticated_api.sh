#!/usr/bin/env bash
set -euo pipefail

cd ~/waste-platform

LOGIN_JSON="$(curl -fsS -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@cmep.dev","password":"Admin123!"}')"

TOKEN="$(printf '%s' "$LOGIN_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["accessToken"])')"

echo "=== Prihlasenie ==="
echo "OK: access token ziskany (token sa nevypisuje)"

for PATH in "/api/v1/auth/me" "/api/v1/users" "/api/v1/listings"; do
  echo ""
  echo "=== GET $PATH ==="
  curl -sS \
    -H "Authorization: Bearer $TOKEN" \
    -w "
HTTP status: %{http_code}
" \
    "http://localhost:8001$PATH"
done
