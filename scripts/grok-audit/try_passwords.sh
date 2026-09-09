#!/usr/bin/env bash
set -u

cd ~/waste-platform

EMAIL="admin@cmep-bootstrap.dev"

for PWD in "ChangeMe123" "admin" "admin123" "bootstrap" "cmep" "password123" "P@ssw0rd" "waste" "waste123"; do
    RESULT=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d "{"email":"$EMAIL","password":"$PWD"}")
    
    if echo "$RESULT" | grep -q "accessToken"; then
        echo "SUCCESS! Heslo: $PWD"
        echo "$RESULT" | python3 -m json.tool
        exit 0
    else
        echo "FAIL: $PWD"
    fi
done

echo ""
echo "Ziadne z testovanych hesiel nefungovalo"
