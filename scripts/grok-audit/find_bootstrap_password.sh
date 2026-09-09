#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. .env subor ==="
cat .env | grep -i "password|admin|bootstrap" || echo "ziadne matche"

echo ""
echo "=== 2. .env.example ==="
cat .env.example | grep -i "password|admin" || echo "ziadne matche"

echo ""
echo "=== 3. Config.py - hladanie default hesla ==="
grep -n "PASSWORD|password" app/core/config.py | head -20

echo ""
echo "=== 4. Vsetky .env subory ==="
find . -name ".env*" -type f 2>/dev/null | head -10

echo ""
echo "=== 5. Bootstrap scripty ==="
find . -name "*bootstrap*" -o -name "*seed*" -o -name "*init*user*" 2>/dev/null | grep -v node_modules | grep -v ".git" | head -10

echo ""
echo "=== 6. Hash hesla v DB ==="
python3 <<'PY'
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./var/cmep.db")
Session = sessionmaker(bind=engine)
session = Session()

result = session.execute(text("""
    SELECT id, email, password_hash 
    FROM users 
    WHERE email IN ('admin@cmep-bootstrap.dev', 'mefoku52@gmail.com')
""")).fetchall()

for row in result:
    print(f"Email: {row[1]}")
    print(f"Hash: {row[2][:100]}..." if len(str(row[2])) > 100 else f"Hash: {row[2]}")
    print()
PY
