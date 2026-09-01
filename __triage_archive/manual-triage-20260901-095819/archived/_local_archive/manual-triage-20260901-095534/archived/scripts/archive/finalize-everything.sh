#!/bin/bash
# ==============================================================================
# finalize-everything.sh — Dokončenie CMEP do produkčného stavu
# ==============================================================================
set -euo pipefail

ROOT="$HOME/waste-platform"
cd "$ROOT"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()  { echo -e "${GREEN}[FINAL]${NC} $1"; }
warn(){ echo -e "${YELLOW}[FINAL]${NC} $1"; }
err() { echo -e "${RED}[FINAL]${NC} $1"; }

# ==============================================================================
# 1. HEALTH ROUTER — pridať do main.py ak chýba
# ==============================================================================
if ! grep -q "health_router" app/main.py 2>/dev/null; then
    sed -i '/from app.shared.presentation.api_router import api_router/a \
from app.shared.presentation.health_router import router as health_router' app/main.py
    sed -i '/app.include_router(api_router/i \    app.include_router(health_router)' app/main.py
    ok "Health router pripojený na /health"
else
    ok "Health router už je v main.py"
fi

# ==============================================================================
# 2. SILNÉ JWT KĽÚČE — vygenerovať ak sú weak/missing
# ==============================================================================
JWT_NOW=$(grep "^JWT_SECRET_KEY=" .env | cut -d= -f2- | tr -d ' ')
if [ -z "$JWT_NOW" ] || [ "$JWT_NOW" = "change-me" ] || [ "$JWT_NOW" = "change-me-super-secret-key" ]; then
    NEW_SEC=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    NEW_REF=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    sed -i "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_SEC/" .env
    sed -i "s/^JWT_REFRESH_SECRET_KEY=.*/JWT_REFRESH_SECRET_KEY=$NEW_REF/" .env
    ok "Vygenerované silné JWT kľúče (64 bytes)"
else
    ok "JWT kľúče sú už nastavené"
fi

# ==============================================================================
# 3. DB INIT — vytvoriť tabuľky + seed admina
# ==============================================================================
cat > "$ROOT/seed_database.py" << 'PYEOF'
import asyncio
from sqlalchemy import select
from app.shared.infrastructure.db.session import engine, SessionLocal
from app.shared.infrastructure.db.base import Base
from app.shared.infrastructure.db.register_models import *
from app.modules.users.infrastructure.models import UserModel
from app.shared.application.passwords import PasswordService
from datetime import datetime, timezone

async def init():
    print("   [DB] Vytváram tabuľky...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   [DB] Tabuľky hotové")

    async with SessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.email == "admin@cmep.local")
        )
        if result.scalar_one_or_none():
            print("   [DB] Admin už existuje")
            return

        ps = PasswordService()
        admin = UserModel(
            id="00000000-0000-0000-0000-000000000001",
            status="active",
            email="admin@cmep.local",
            password_hash=ps.hash_password("Admin123!"),
            first_name="System",
            last_name="Admin",
            display_name="Administrator",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(admin)
        await session.commit()
        print("   [DB] Admin vytvorený: admin@cmep.local / Admin123!")

if __name__ == "__main__":
    asyncio.run(init())
PYEOF

python3 "$ROOT/seed_database.py" && ok "Databáza inicializovaná" || err "DB init zlyhal"

# ==============================================================================
# 4. FRONTEND BUILD
# ==============================================================================
if [ -d "$ROOT/apps/web" ]; then
    cd "$ROOT/apps/web"
    if [ ! -d "node_modules" ]; then
        warn "Inštalujem npm balíky..."
        npm install || warn "npm install zlyhal"
    fi
    npm run build 2>/dev/null && ok "Frontend zbuildený" || warn "Frontend build vynechaný (skontroluj ručne)"
    cd "$ROOT"
fi

# ==============================================================================
# 5. TESTY
# ==============================================================================
if command -v pytest >/dev/null 2>&1; then
    python3 -m pytest tests/ -q --tb=line 2>/dev/null && ok "Testy prešli" || warn "Niektoré testy zlyhali (skontroluj výstup vyššie)"
else
    warn "pytest nie je nainštalovaný, preskakujem testy"
fi

# ==============================================================================
# 6. ŠTRUKTÚRA — finálny výpis
# ==============================================================================
echo ""
echo "=================================================================="
echo "  CMEP — FINÁLNA ŠTRUKTÚRA A STAV"
echo "=================================================================="
echo ""
echo "BACKEND MODULES (12):"
find "$ROOT/app/modules" -maxdepth 1 -type d | sort | sed 's|.*app/modules/|  📦 |' | grep -v "__pycache__"
echo ""
echo "SHARED:"
echo "  🔧 app/shared/domain          — entity, enums, repositories (ABC)"
echo "  🔧 app/shared/application     — passwords, clock, uuid, side effects"
echo "  🔧 app/shared/infrastructure  — db, email, security (JWT + Redis), rate limit"
echo "  🔧 app/shared/presentation    — api_router, auth deps, exception handlers, health, metrics"
echo ""
echo "FRONTEND:"
echo "  🎨 apps/web/src/app/          — Next.js App Router"
echo "  🎨 apps/web/src/features/     — auth, companies, listings, inquiries, admin..."
echo ""
echo "TESTS:"
ls -1 "$ROOT"/tests/test_*.py 2>/dev/null | sed 's|.*/|  🧪 |' || echo "  (žiadne testy)"
echo ""
echo "INFRA:"
echo "  🐳 docker-compose.yml"
echo "  🐳 docker-compose.production.yml"
echo "  📊 docker-compose.monitoring.yml"
echo ""
echo "ENDPOINTS:"
echo "  🌐 http://localhost:8000         — API root"
echo "  📖 http://localhost:8000/docs    — Swagger UI"
echo "  ❤️  http://localhost:8000/health  — Health check"
echo "  📈 http://localhost:8000/internal/metrics — Metrics (dev/staging only)"
echo ""
echo "AUTH:"
echo "  👤 Admin: admin@cmep.local / Admin123!"
echo "  🔑 JWT:    $(grep '^JWT_SECRET_KEY=' .env | cut -d= -f1)=*** (silný)"
echo ""
echo "Spustenie celej platformy:"
echo "  bash ~/waste-platform/run-everything.sh"
echo "=================================================================="
