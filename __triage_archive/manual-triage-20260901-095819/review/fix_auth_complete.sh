#!/bin/bash
# KOMPLETNÁ OPRAVA AUTHENTIKÁCIE PRE WASTE-PLATFORM

set -e

echo "=========================================="
echo "OPRAVA AUTHENTIKÁCIE – WASTE-PLATFORM"
echo "=========================================="

# 1. PRIDANIE CHÝBAJÚCEHO STĹPCA do DB
echo ""
echo "[1] Pridanie stĺpca hashed_password do tabuľky users..."

psql -d cmep << 'SQL'
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='hashed_password'
    ) THEN
        ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255);
        RAISE NOTICE 'Stĺpec hashed_password bol pridaný.';
    ELSE
        RAISE NOTICE 'Stĺpec hashed_password už existuje.';
    END IF;
END $$;
SQL

# 2. SKOPÍROVANIE ÚDAJOV z password_hash do hashed_password
echo ""
echo "[2] Kopírovanie hesiel do hashed_password..."

psql -d cmep -c "UPDATE users SET hashed_password = password_hash WHERE hashed_password IS NULL;"

# 3. KONTROLA, ČI EXISTUJE get_async_session v session.py
echo ""
echo "[3] Kontrola get_async_session v session.py..."

if ! grep -q "get_async_session" app/shared/infrastructure/db/session.py; then
    echo 'get_async_session = get_db_session' >> app/shared/infrastructure/db/session.py
    echo "✅ get_async_session pridané do session.py"
else
    echo "✅ get_async_session už existuje"
fi

# 4. VYTVORENIE TESTOVACIEHO POUŽÍVATEĽA (ak neexistuje)
echo ""
echo "[4] Vytvorenie testovacieho používateľa..."

HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'test123', bcrypt.gensalt()).decode())")

psql -d cmep << SQL
INSERT INTO users (id, email, password_hash, hashed_password, first_name, last_name, status, created_at, updated_at)
SELECT 
    gen_random_uuid()::text,
    'test@example.com',
    '$HASH',
    '$HASH',
    'Test',
    'User',
    'active',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'test@example.com'
);
SQL

echo "✅ Testovací používateľ: test@example.com / test123"

# 5. AKTIVÁCIA VŠETKÝCH POUŽÍVATEĽOV
echo ""
echo "[5] Aktivácia všetkých používateľov..."

psql -d cmep -c "UPDATE users SET status = 'active' WHERE status IS NULL OR status != 'active';"

# 6. REŠTARTOVANIE BACKENDU
echo ""
echo "[6] Reštart backendu..."

pkill -f "uvicorn" 2>/dev/null || true
sleep 2

cd ~/waste-platform
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 >> ~/cmep-backend.log 2>&1 &
sleep 3

# 7. TESTOVANIE PRIHLÁSENIA
echo ""
echo "[7] Testovanie prihlásenia..."

curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'access_token' in data:
        print('✅ PRIHLÁSENIE ÚSPEŠNÉ!')
        print('Token:', data.get('access_token', '')[:50] + '...')
    elif 'detail' in data:
        print('❌ Chyba:', data.get('detail'))
    else:
        print('❌ Neznáma odpoveď:', data)
except:
    print('❌ Chyba pri parsovaní odpovede')
"

echo ""
echo "=========================================="
echo "   HOTOVO!"
echo "=========================================="
echo ""
echo "Prihlasovacie údaje:"
echo "  Email: test@example.com"
echo "  Heslo: test123"
echo ""
echo "Swagger UI: http://localhost:8001/docs"
echo "Frontend:   http://localhost:3001"
echo ""
