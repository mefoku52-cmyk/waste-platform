#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Kontrola Alembic konfiguracie ==="
head -30 alembic.ini

echo ""
echo "=== 2. Zoznam migracii ==="
ls -la migrations/ 2>/dev/null | head -20

echo ""
echo "=== 3. Stav databazy (SQL dotaz) ==="
psql -U u0_a388 -h localhost -d cmep -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"

echo ""
echo "=== 4. Aplikacia migracii (Alembic upgrade) ==="
# Aktivuj venv ak existuje
if [ -f scripts/grok-audit/test-venv/bin/activate ]; then
    source scripts/grok-audit/test-venv/bin/activate
fi

# Spusti alembic upgrade
alembic upgrade head 2>&1

echo ""
echo "=== 5. Overenie - tabulky po migracii ==="
psql -U u0_a388 -h localhost -d cmep -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"

echo ""
echo "=== 6. Vytvorenie admin pouzivatel'a ==="
python3 <<'PY'
import asyncio
import sys
sys.path.insert(0, '.')

from app.shared.infrastructure.db.session import get_db_session
from app.modules.users.domain.user import User
from app.modules.auth.infrastructure.services.password_service import PasswordService

async def create_admin():
    async with get_db_session() as session:
        password_service = PasswordService()
        hashed = await password_service.hash_password("Admin123!")
        
        user = User.create(
            email="admin@cmeplatform.com",
            password_hash=hashed,
            first_name="Admin",
            last_name="User",
            is_email_verified=True,
        )
        
        session.add(user)
        await session.commit()
        print(f"Created: {user.email} (id={user.id})")

asyncio.run(create_admin())
PY

echo ""
echo "=== 7. Test login ==="
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cmeplatform.com","password":"Admin123!"}' | python3 -m json.tool
