#!/data/data/com.termux/files/usr/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

if [ ! -f "app/main.py" ]; then
    log_error "Spustiť v koreňovom adresári projektu (waste-platform)"
    exit 1
fi

# 1. Git init
if [ ! -d ".git" ]; then
    log_info "Inicializácia gitu..."
    git init
else
    log_info "Git už inicializovaný."
fi

# 2. .gitignore
if [ ! -f ".gitignore" ]; then
    log_info "Vytváram .gitignore..."
    cat <<'GITIGNORE' > .gitignore
__pycache__/
*.pyc
.env
.venv/
venv/
alembic/versions/
*.db
*.sqlite3
node_modules/
.next/
dist/
.DS_Store
GITIGNORE
else
    log_info ".gitignore už existuje."
fi

# 3. requirements.txt (PURE PYTHON - žiadna kompilácia)
log_info "Vytváram requirements.txt (čistý Python)..."
cat <<'REQ' > requirements.txt
fastapi
uvicorn
sqlalchemy
aiosqlite
alembic
PyJWT
passlib
python-multipart
python-dotenv
pytest
pytest-asyncio
httpx
REQ

# 4. pyproject.toml
log_info "Vytváram pyproject.toml..."
cat <<'PYPROJ' > pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "waste-platform"
version = "0.1.0"
description = "Platform for circular materials exchange"
dependencies = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "aiosqlite",
    "alembic",
    "PyJWT",
    "passlib",
    "python-multipart",
    "python-dotenv",
]
[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "httpx"]
PYPROJ

# 5. Virtuálne prostredie
if [ ! -d ".venv" ]; then
    log_info "Vytváram virtuálne prostredie..."
    python3 -m venv .venv
else
    log_info "Virtuálne prostredie už existuje."
fi

source .venv/bin/activate

# 6. Inštalácia setuptools a wheel
log_info "Inštalujem setuptools a wheel..."
pip install --upgrade pip setuptools wheel

# 7. Inštalácia závislostí (čistý Python, žiadna kompilácia)
log_info "Inštalujem závislosti (čistý Python)..."
export MAX_JOBS=1
pip install --no-cache-dir --prefer-binary -r requirements.txt

# 8. Oprava api_router.py
log_info "Opravujem app/shared/presentation/api_router.py..."
cat <<'API_ROUTER' > app/shared/presentation/api_router.py
from fastapi import APIRouter

from app.modules.auth.presentation.router import router as auth_router
from app.modules.users.presentation.router import router as users_router
from app.modules.companies.presentation.router import router as companies_router
from app.modules.company_memberships.presentation.router import router as company_memberships_router
from app.shared.presentation.health_router import router as health_router
from app.shared.presentation.metrics_router import router as metrics_router

router = APIRouter()
router.include_router(health_router)
router.include_router(metrics_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(companies_router)
router.include_router(company_memberships_router)
API_ROUTER

# 9. Nastavenie .env
if [ ! -f ".env" ]; then
    log_info "Vytváram .env s DATABASE_URL pre SQLite..."
    cat <<'ENV' > .env
DATABASE_URL=sqlite+aiosqlite:///./waste.db
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
ENV
else
    log_info ".env už existuje, nastavujem DATABASE_URL..."
    sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite+aiosqlite:///./waste.db|' .env
fi

# 10. Alembic
log_info "Inicializujem Alembic (ak treba)..."
if [ ! -d "alembic" ]; then
    alembic init alembic
else
    log_info "Alembic už inicializovaný."
fi

source .env
log_info "Nastavujem sqlalchemy.url v alembic.ini na ${DATABASE_URL}"
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DATABASE_URL}|" alembic.ini

log_info "Upravujem alembic/env.py..."
cp alembic/env.py alembic/env.py.bak
sed -i '/target_metadata = None/i from app.shared.infrastructure.db.base import Base\nfrom app.modules.auth.infrastructure import models\nfrom app.modules.users.infrastructure import models\nfrom app.modules.companies.infrastructure import models\nfrom app.modules.company_memberships.infrastructure import models' alembic/env.py
sed -i 's/target_metadata = None/target_metadata = Base.metadata/' alembic/env.py

log_info "Generujem prvú migráciu..."
alembic revision --autogenerate -m "initial"

log_info "Aplikujem migráciu na SQLite..."
alembic upgrade head

# 11. Oprava importov v auth servisoch (python-jose → jwt)
log_info "Opravujem importy v auth službách (PyJWT namiesto python-jose)..."
# Skontrolujeme, či existuje auth/application/services.py a upravíme importy
if [ -f "app/modules/auth/application/services.py" ]; then
    sed -i 's/from jose import JWTError, jwt/import jwt\nfrom jwt import InvalidTokenError/' app/modules/auth/application/services.py
    sed -i 's/jwt\.encode(/jwt.encode(/g' app/modules/auth/application/services.py
    sed -i 's/jwt\.decode(/jwt.decode(/g' app/modules/auth/application/services.py
    sed -i 's/JWTError/InvalidTokenError/g' app/modules/auth/application/services.py
fi

# 12. Oprava shared/infrastructure/security/jwt_service.py
if [ -f "app/shared/infrastructure/security/jwt_service.py" ]; then
    sed -i 's/from jose import jwt/import jwt/' app/shared/infrastructure/security/jwt_service.py
    sed -i 's/jwt\.encode(/jwt.encode(/g' app/shared/infrastructure/security/jwt_service.py
    sed -i 's/jwt\.decode(/jwt.decode(/g' app/shared/infrastructure/security/jwt_service.py
fi

# 13. Spustenie backendu
log_info "Spúšťam backend (uvicorn)..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > uvicorn.log 2>&1 &
BACKEND_PID=$!
sleep 5

# 14. Overenie
log_info "Overujem /health..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    log_info "/health OK"
else
    log_error "/health zlyhal"
    cat uvicorn.log
    exit 1
fi

log_info "Overujem /docs..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
    log_info "/docs OK"
else
    log_warn "/docs nevrátil 200, preskakujem"
fi

log_info "Overujem /openapi.json..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/openapi.json | grep -q "200"; then
    log_info "/openapi.json OK"
else
    log_error "/openapi.json zlyhal"
    cat uvicorn.log
    exit 1
fi

log_info "Fáza 0 (Termux, čistý Python) úspešne dokončená!"
log_info "Backend beží na PID $BACKEND_PID, logy v uvicorn.log"
echo $BACKEND_PID > backend.pid

# 15. Rýchly test API
log_info "Testujem dostupnosť endpointov..."
curl -s http://localhost:8000/docs | head -20

deactivate
exit 0
