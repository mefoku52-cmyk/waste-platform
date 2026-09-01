#!/bin/bash
set -e

echo "=== 1. Zápis fixných JWT kľúčov do .env ==="
sed -i '/JWT_SECRET_KEY/d' .env
sed -i '/JWT_REFRESH_SECRET_KEY/d' .env
echo 'JWT_SECRET_KEY="super_tajny_kluc_pre_vyvoj_123!"' >> .env
echo 'JWT_REFRESH_SECRET_KEY="dalsi_super_tajny_kluc_456!"' >> .env

echo "=== 2. Získanie nového JWT Tokenu ==="
RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "StrongPassword123!"
  }')

TOKEN=$(echo $RESPONSE | grep -o '"accessToken":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Chyba: Nepodarilo sa získať token. Odpoveď servera:"
  echo "$RESPONSE"
  exit 1
fi

echo "Token úspešne získaný!"

echo "=== 3. Testovanie /api/v1/users/me ==="
curl -i -X GET http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

