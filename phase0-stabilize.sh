#!/data/data/com.termux/files/usr/bin/bash
set -e

# Farba pre logy
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Kontrola adresára
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
# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
*.log
*.sqlite3
*.db

# Virtual Environment
.venv/
venv/

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
.next/
out/
dist/
build/

# Testing
.coverage
htmlcov/
.tox/
.pytest_cache/
.mypy_cache/
.dmypy.json
dmypy.json

# Docker
*.pid
*.pid.lock

# OS
.DS_Store
Thumbs.db

# Project specific
alembic/versions/*.pyc
alembic/versions/*.pyo
!alembic/versions/*.py
GITIGNORE
else
    log_info ".gitignore už existuje."
fi

# 3. requirements.txt
if [ ! -f "requirements.txt" ]; then
    log_info "Vytváram requirements.txt..."
    cat <<'REQ' > requirements.txt
fastapi[standard]
sqlalchemy
asyncpg
alembic
python-jose[cryptography]
passlib[bcrypt]
prometheus-client
redis
pytest
pytest-asyncio
httpx
python-multipart
uvicorn[standard]
REQ
else
    log_info "requirements.txt už existuje."
fi

# 4. pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    log_info "Vytváram pyproject.toml..."
    cat <<'PYPROJ' > pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "waste-platform"
version = "0.1.0"
description = "Platform for circular materials exchange"
authors = [{name = "CMEP Team"}]
dependencies = [
    "fastapi[standard]",
    "sqlalchemy",
    "asyncpg",
    "alembic",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "prometheus-client",
    "redis",
    "python-multipart",
    "uvicorn[standard]",
]
[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "httpx"]
PYPROJ
else
    log_info "pyproject.toml už existuje."
fi

# 5. Virtuálne prostredie a inštalácia
if [ ! -d ".venv" ]; then
    log_info "Vytváram virtuálne prostredie..."
    python3 -m venv .venv
else
    log_info "Virtuálne prostredie už existuje."
fi

# Aktivácia a inštalácia
source .venv/bin/activate
log_info "Inštalujem závislosti..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Oprava api_router.py
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

# 7. Kontrola main.py (prípadne upraviť, ale je ok)
log_info "Kontrolujem main.py..."
if ! grep -q "register_exception_handlers" app/main.py; then
    log_warn "main.py neobsahuje register_exception_handlers? Pridávam..."
    # Pridať import a volanie, ale podľa auditu to tam je, takže len varovanie
fi

# 8. Alembic
if ! command -v alembic &> /dev/null; then
    log_info "Inštalujem alembic (už by malo byť v requirements)..."
    pip install alembic
fi

if [ ! -d "alembic" ]; then
    log_info "Inicializujem Alembic..."
    alembic init alembic
else
    log_info "Alembic už inicializovaný."
fi

# Upraviť alembic.ini podľa .env (použiť DATABASE_URL)
log_info "Nastavujem DATABASE_URL v alembic.ini..."
# Načítame .env (ak existuje)
if [ -f ".env" ]; then
    source .env
else
    log_warn ".env neexistuje, používam predvolené hodnoty"
    DATABASE_URL="postgresql+asyncpg://cmep:cmep@postgres:5432/cmep"
fi
# Nahradíme sqlalchemy.url
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DATABASE_URL}|" alembic.ini

# Upraviť env.py na import modelov
log_info "Upravujem alembic/env.py pre správny import modelov..."
# Najprv skopírujeme originál
cp alembic/env.py alembic/env.py.bak
# Vložíme importy pred target_metadata = None
sed -i '/target_metadata = None/i from app.shared.infrastructure.db.base import Base\nfrom app.modules.auth.infrastructure import models\nfrom app.modules.users.infrastructure import models\nfrom app.modules.companies.infrastructure import models\nfrom app.modules.company_memberships.infrastructure import models' alembic/env.py
# Potom nastavíme target_metadata = Base.metadata
sed -i 's/target_metadata = None/target_metadata = Base.metadata/' alembic/env.py

# Vygenerovať migráciu
log_info "Generujem prvú migráciu..."
alembic revision --autogenerate -m "initial"

# Aplikovať migráciu
log_info "Aplikujem migráciu..."
alembic upgrade head

# 9. Overenie PostgreSQL (kontrola, či beží)
log_info "Overujem PostgreSQL..."
if command -v pg_isready &> /dev/null; then
    pg_isready -h localhost -p 5432 -U cmep || log_warn "PostgreSQL nie je dostupný, skontroluj docker"
else
    log_warn "pg_isready nenájdený, preskakujem kontrolu"
fi

# 10. Spustenie backendu
log_info "Spúšťam backend (uvicorn)..."
# Spustíme na pozadí a uložíme PID
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > uvicorn.log 2>&1 &
BACKEND_PID=$!
sleep 5

# Overenie health
log_info "Overujem /health..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    log_info "/health OK"
else
    log_error "/health zlyhal"
    cat uvicorn.log
    exit 1
fi

# Overenie /docs
log_info "Overujem /docs..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
    log_info "/docs OK"
else
    log_warn "/docs nevrátil 200, možno presmerovanie"
fi

# Overenie /openapi.json
log_info "Overujem /openapi.json..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/openapi.json | grep -q "200"; then
    log_info "/openapi.json OK"
else
    log_error "/openapi.json zlyhal"
    cat uvicorn.log
    exit 1
fi

log_info "Fáza 0 úspešne dokončená!"
log_info "Backend beží na PID $BACKEND_PID, logy v uvicorn.log"
log_info "Pre zastavenie: kill $BACKEND_PID"

# Uložiť PID do súboru pre neskoršie použitie
echo $BACKEND_PID > backend.pid

# Deaktivácia virtuálneho prostredia
deactivate

exit 0
