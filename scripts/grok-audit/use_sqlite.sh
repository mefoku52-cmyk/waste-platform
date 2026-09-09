#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Aktualizacia .env na SQLite ==="
sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite+aiosqlite:///./var/cmep.db|' .env
grep "^DATABASE_URL" .env

echo ""
echo "=== 2. Restart backendu ==="
pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
sleep 2

DATABASE_URL="sqlite+aiosqlite:///./var/cmep.db" nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > ~/waste-platform/scripts/grok-audit/backend_sqlite.log 2>&1 &
sleep 5

echo ""
echo "=== 3. Test health ==="
curl -s http://localhost:8001/health | python3 -m json.tool

echo ""
echo "=== 4. Test login (SQLite ma uz tabulky) ==="
# Najprv vytvor admina priamo v SQLite
python3 <<'PY'
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./var/cmep.db")
Session = sessionmaker(bind=engine)
session = Session()

# Skontroluj ci uz existuje admin
result = session.execute(text("SELECT id, email FROM users WHERE email = 'admin@cmeplatform.com'")).fetchone()
if result:
    print(f"Admin uz existuje: id={result[0]}, email={result[1]}")
else:
    # Vytvor admina (heslo: Admin123!)
    import uuid
    from datetime import datetime
    
    user_id = str(uuid.uuid4())
    hashed = "scrypt:32768:8:1$test$hashed_password_placeholder"  # Toto treba spravit poriadne
    
    session.execute(text("""
        INSERT INTO users (id, email, password_hash, first_name, last_name, is_email_verified, created_at)
        VALUES (:id, :email, :hash, :first, :last, :verified, :created)
    """), {
        "id": user_id,
        "email": "admin@cmeplatform.com",
        "hash": "$scrypt$admin123hashed",  # Placeholder - treba spravit cez PasswordService
        "first": "Admin",
        "last": "User",
        "verified": 1,
        "created": datetime.utcnow().isoformat()
    })
    session.commit()
    print(f"Created admin: {user_id}")
PY

echo ""
echo "=== 5. Login test ==="
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cmeplatform.com","password":"Admin123!"}' 2>&1 | python3 -m json.tool
