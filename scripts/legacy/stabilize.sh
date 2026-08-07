#!/data/data/com.termux/files/usr/bin/bash

# Stabilizačný skript pre projekt
# Verzia: 1.0.0
# Dátum: $(date +%Y-%m-%d)

set -euo pipefail

# Farby pre výstup
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logovacie funkcie
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Kontrola prostredia
check_environment() {
    log_info "Kontrola prostredia..."
    
    # Kontrola Termux
    if ! command -v termux-info &> /dev/null; then
        log_error "Tento skript vyžaduje Termux prostredie"
        exit 1
    fi
    
    # Kontrola Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 nie je nainštalovaný"
        log_info "Inštalujem Python..."
        pkg install python3 -y
    fi
    
    # Kontrola pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 nie je nainštalovaný"
        log_info "Inštalujem pip..."
        pkg install python3-pip -y
    fi
    
    # Kontrola Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js nie je nainštalovaný"
        log_info "Inštalujem Node.js..."
        pkg install nodejs -y
    fi
    
    # Kontrola npm
    if ! command -v npm &> /dev/null; then
        log_error "npm nie je nainštalovaný"
        log_info "Inštalujem npm..."
        pkg install nodejs-npm -y
    fi
    
    # Kontrola Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker nie je nainštalovaný"
        log_info "Inštalujem Docker..."
        pkg install docker -y
    fi
    
    # Kontrola Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose nie je nainštalovaný"
        log_info "Inštalujem Docker Compose..."
        pkg install docker-compose -y
    fi
    
    # Kontrola PostgreSQL
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL nie je nainštalovaný"
        log_info "Inštalujem PostgreSQL..."
        pkg install postgresql -y
    fi
    
    log_success "Prostredie je pripravené"
}

# Vytvorenie štruktúry projektu
create_project_structure() {
    log_info "Vytváram štruktúru projektu..."
    
    # Hlavné adresáre
    mkdir -p backend/app/{api,core,models,schemas,services,repositories,utils,alembic}
    mkdir -p backend/app/api/{v1,admin,websocket}
    mkdir -p backend/app/core/{security,config,database,logging,metrics}
    mkdir -p backend/app/models/{base,user,company,listing,transaction}
    mkdir -p backend/app/schemas/{user,company,listing,transaction,common}
    mkdir -p backend/app/services/{user,company,listing,transaction,notification}
    mkdir -p backend/app/repositories/{base,user,company,listing,transaction}
    mkdir -p backend/app/utils/{validators,helpers,decorators,context}
    mkdir -p backend/app/alembic/versions
    mkdir -p backend/scripts
    mkdir -p backend/tests/{unit,integration,api,fixtures}
    mkdir -p backend/logs
    mkdir -p backend/data
    
    mkdir -p frontend/app/{api,auth,components,context,hooks,lib,types,utils,pages,styles}
    mkdir -p frontend/app/api/{client,middleware,interceptors}
    mkdir -p frontend/app/auth/{login,register,forgot-password,reset-password}
    mkdir -p frontend/app/components/{ui,layout,forms,tables,cards,modals}
    mkdir -p frontend/app/components/ui/{buttons,inputs,dropdowns,modals,alerts}
    mkdir -p frontend/app/context/{auth,theme,notification,company}
    mkdir -p frontend/app/hooks/{auth,api,form,data}
    mkdir -p frontend/app/lib/{validators,formatters,helpers,constants}
    mkdir -p frontend/app/pages/{dashboard,companies,listings,users,admin,settings}
    mkdir -p frontend/app/styles/{components,layouts,utilities}
    mkdir -p frontend/public/{images,icons,fonts}
    
    mkdir -p docker/{backend,frontend,nginx,postgres,redis,prometheus,grafana}
    mkdir -p docker/nginx/{conf.d,ssl,logs}
    mkdir -p docker/postgres/{init,data,backups}
    mkdir -p docker/redis/{data,conf}
    mkdir -p docker/prometheus/{config,data,rules}
    mkdir -p docker/grafana/{config,data,dashboards}
    
    mkdir -p docs/{api,architecture,deployment,development,user}
    mkdir -p scripts/{deploy,backup,monitor,test}
    mkdir -p .github/workflows
    
    log_success "Štruktúra projektu vytvorená"
}

# Git inicializácia
init_git() {
    log_info "Inicializujem Git..."
    
    if [ ! -d .git ]; then
        git init
        git config user.email "developer@recyclehub.sk"
        git config user.name "RecycleHub Developer"
        log_success "Git inicializovaný"
    else
        log_info "Git už existuje"
    fi
}

# Vytvorenie .gitignore
create_gitignore() {
    log_info "Vytváram .gitignore..."
    
    cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
pythonenv*
*.egg-info/
dist/
build/
*.egg
*.log
*.pid
*.pid.lock
*.sqlite
*.db
*.sqlite3
.coverage
.coverage.*
htmlcov/
.pytest_cache/
.mypy_cache/
.dmypy.json
dmypy.json
*.pyre
*.pytypes

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
.next/
out/
dist/
.cache/
.vercel
*.tsbuildinfo

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
.env.*.local
.env.backup
*.env.backup

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
.velite
.velite-dist

# Docker
*.pid
docker-compose.override.yml
docker-compose.local.yml

# PostgreSQL
*.pgdata
*.dump
postgresql-*.log

# Redis
*.rdb
*.aof
*.log

# Prometheus
prometheus.db
prometheus.log

# Grafana
grafana.db

# Logs
logs/
*.log
*.log.*
backend/logs/
frontend/logs/
docker/nginx/logs/

# Data
data/
*.db
*.sqlite
*.sqlite-journal
backend/data/
*.pkl
*.pickle
*.h5
*.model

# Backups
*.backup
*.bak
backups/
*.backup.sql
*.dump.sql
*.tar.gz
*.tgz
*.zip

# Temporary
tmp/
temp/
*.tmp
*.temp
*.cache
*.cached
*.lock
*.lock.*
*.pid.lock

# Secrets
*.pem
*.key
*.crt
*.csr
*.jks
*.keystore
*.p12
*.pfx
*.pwd
.secrets/
secrets/
*.secret
GITIGNORE
    
    log_success ".gitignore vytvorený"
}

# Vytvorenie requirements.txt
create_requirements() {
    log_info "Vytváram requirements.txt..."
    
    cat > backend/requirements.txt << 'REQUIREMENTS'
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.4.2
pydantic-settings==2.0.3

# Database
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.6
python-email-validator==2.0.0
email-validator==2.0.0

# API
httpx==0.25.0
requests==2.31.0
python-json-logger==2.0.7

# Background tasks
celery==5.3.4
redis==5.0.1
flower==2.0.1

# Monitoring
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0

# Utils
python-dateutil==2.8.2
pytz==2023.3
typing-extensions==4.8.0
pillow==10.1.0
python-slugify==8.0.1

# Development
pytest==7.4.2
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.11.1
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.6.1
pre-commit==3.5.0

# Production
gunicorn==21.2.0
uvloop==0.19.0
httptools==0.6.1
python-multipart==0.0.6

# Additional
pyyaml==6.0.1
toml==0.10.2
jinja2==3.1.2
markdown==3.5.1
REQUIREMENTS
    
    log_success "requirements.txt vytvorený"
}

# Vytvorenie pyproject.toml
create_pyproject() {
    log_info "Vytváram pyproject.toml..."
    
    cat > backend/pyproject.toml << 'PYPROJECT'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "recyclehub-backend"
version = "1.0.0"
description = "RecycleHub backend API pre obehové hospodárstvo"
readme = "README.md"
requires-python = ">=3.11"
license = {file = "LICENSE"}
authors = [
    {name = "RecycleHub Team", email = "team@recyclehub.sk"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "License :: Other/Proprietary License",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.4.0",
    "pydantic-settings>=2.0.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "asyncpg>=0.29.0",
    "psycopg2-binary>=2.9.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "email-validator>=2.0.0",
    "httpx>=0.25.0",
    "celery>=5.3.0",
    "redis>=5.0.0",
    "prometheus-client>=0.19.0",
    "python-dateutil>=2.8.0",
    "pytz>=2023.3",
    "typing-extensions>=4.8.0",
    "python-json-logger>=2.0.0",
    "gunicorn>=21.0.0",
    "uvloop>=0.19.0",
    "httptools>=0.6.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "black>=23.11.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.6.0",
    "pre-commit>=3.5.0",
]

[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=app --cov-report=html --cov-report=term"
testpaths = [
    "tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["app"]
omit = ["*/alembic/*", "*/tests/*", "*/scripts/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
PYPROJECT
    
    log_success "pyproject.toml vytvorený"
}

# Inštalácia závislostí
install_dependencies() {
    log_info "Inštalujem Python závislosti..."
    
    cd backend
    if [ ! -d venv ]; then
        python3 -m venv venv
        log_success "Virtuálne prostredie vytvorené"
    fi
    
    source venv/bin/activate || source venv/Scripts/activate || true
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    cd ..
    
    log_success "Python závislosti nainštalované"
}

# Vytvorenie Docker súborov
create_docker_files() {
    log_info "Vytváram Docker súbory..."
    
    # Backend Dockerfile
    cat > docker/backend/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Inštalácia systémových závislostí
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopírovanie requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírovanie kódu
COPY backend/ .

# Vytvorenie užívateľa
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Spustenie
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
DOCKERFILE
    
    # Frontend Dockerfile
    cat > docker/frontend/Dockerfile << 'DOCKERFILE'
FROM node:18-alpine

WORKDIR /app

# Kopírovanie package.json
COPY frontend/package*.json ./
RUN npm ci

# Kopírovanie kódu
COPY frontend/ .

# Build
RUN npm run build

# Spustenie
CMD ["npm", "start"]
DOCKERFILE
    
    # Nginx Dockerfile
    cat > docker/nginx/Dockerfile << 'DOCKERFILE'
FROM nginx:alpine

# Kopírovanie konfigurácie
COPY docker/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx/ssl /etc/nginx/ssl

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80 443
DOCKERFILE
    
    log_success "Docker súbory vytvorené"
}

# Vytvorenie docker-compose.yml
create_docker_compose() {
    log_info "Vytváram docker-compose.yml..."
    
    cat > docker-compose.yml << 'DOCKERCOMPOSE'
version: '3.8'

services:
  postgres:
    build:
      context: .
      dockerfile: docker/postgres/Dockerfile
    container_name: recyclehub-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-recyclehub}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-recyclehub}
      POSTGRES_DB: ${POSTGRES_DB:-recyclehub}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d
      - ./docker/postgres/backups:/backups
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-recyclehub}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - recyclehub-network
    restart: unless-stopped

  redis:
    build:
      context: .
      dockerfile: docker/redis/Dockerfile
    container_name: recyclehub-redis
    volumes:
      - redis_data:/data
      - ./docker/redis/conf:/usr/local/etc/redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - recyclehub-network
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile
    container_name: recyclehub-backend
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-recyclehub}:${POSTGRES_PASSWORD:-recyclehub}@postgres:5432/${POSTGRES_DB:-recyclehub}
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY:-supersecretkey}
      ALGORITHM: ${ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      REFRESH_TOKEN_EXPIRE_DAYS: ${REFRESH_TOKEN_EXPIRE_DAYS:-7}
      ENVIRONMENT: ${ENVIRONMENT:-development}
    volumes:
      - ./backend:/app
      - /app/__pycache__
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - recyclehub-network
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: docker/frontend/Dockerfile
    container_name: recyclehub-frontend
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    ports:
      - "3000:3000"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - recyclehub-network
    restart: unless-stopped

  nginx:
    build:
      context: .
      dockerfile: docker/nginx/Dockerfile
    container_name: recyclehub-nginx
    volumes:
      - ./docker/nginx/conf.d:/etc/nginx/conf.d
      - ./docker/nginx/ssl:/etc/nginx/ssl
      - ./docker/nginx/logs:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    networks:
      - recyclehub-network
    restart: unless-stopped

  prometheus:
    build:
      context: .
      dockerfile: docker/prometheus/Dockerfile
    container_name: recyclehub-prometheus
    volumes:
      - ./docker/prometheus/config:/etc/prometheus
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - recyclehub-network
    restart: unless-stopped

  grafana:
    build:
      context: .
      dockerfile: docker/grafana/Dockerfile
    container_name: recyclehub-grafana
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - ./docker/grafana/config:/etc/grafana
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - recyclehub-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  recyclehub-network:
    driver: bridge
DOCKERCOMPOSE
    
    log_success "docker-compose.yml vytvorený"
}

# Vytvorenie .env šablóny
create_env_template() {
    log_info "Vytváram .env šablónu..."
    
    cat > .env.example << 'ENV'
# Database
POSTGRES_USER=recyclehub
POSTGRES_PASSWORD=recyclehub
POSTGRES_DB=recyclehub
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000/ws

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@recyclehub.sk

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Stripe (platby)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# GDPR
GDPR_ENABLED=True
GDPR_COOKIE_CONSENT=True

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
ENV
    
    log_success ".env.example vytvorený"
}

# Vytvorenie základného main.py
create_main_py() {
    log_info "Vytváram main.py..."
    
    cat > backend/app/main.py << 'MAIN'
"""Hlavný vstupný bod FastAPI aplikácie."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging import setup_logging
from app.core.metrics import setup_metrics
from app.models import Base
from app.utils.context import request_context


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Správa životného cyklu aplikácie."""
    # Startup
    setup_logging()
    setup_metrics()
    
    # Vytvorenie databázových tabuliek
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    await engine.dispose()


# Inicializácia aplikácie
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url=None,  # Vypnutie default docs, použijeme vlastné
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Vlastná Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> None:
    """Vlastná Swagger UI stránka."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.PROJECT_NAME} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


# OpenAPI dokumentácia
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint() -> dict:
    """Vlastný OpenAPI endpoint."""
    return get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Kontrola stavu aplikácie."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict:
    """Koreňový endpoint."""
    return {
        "message": f"Vitajte v {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }


# Pridanie middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="recyclehub_session",
)

# Request context middleware
@app.middleware("http")
async def add_request_context(request, call_next):
    """Pridanie kontextu požiadavky."""
    request_id = request.headers.get("X-Request-ID")
    async with request_context(request_id=request_id):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id or "generated"
        return response


# Inklúzia API routerov
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
MAIN
    
    log_success "main.py vytvorený"
}

# Vytvorenie základného routera
create_api_router() {
    log_info "Vytváram API router..."
    
    cat > backend/app/api/v1/router.py << 'ROUTER'
"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    companies,
    listings,
    users,
    health,
    websocket,
)

api_router = APIRouter()

# Inklúzia routerov
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
ROUTER
    
    log_success "api_router.py vytvorený"
}

# Vytvorenie základného config súboru
create_config() {
    log_info "Vytváram config súbor..."
    
    cat > backend/app/core/config.py << 'CONFIG'
"""Konfigurácia aplikácie."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Nastavenia aplikácie."""
    
    # Projekt
    PROJECT_NAME: str = "RecycleHub API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API pre obehové hospodárstvo - správa ponúk druhotných surovín"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Prostredie
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Databáza
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY", min_length=32)
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Allowed hosts
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(default="", env="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@recyclehub.sk", env="EMAIL_FROM")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # Monitoring
    PROMETHEUS_MULTIPROC_DIR: str = Field(
        default="/tmp/prometheus_multiproc",
        env="PROMETHEUS_MULTIPROC_DIR"
    )
    
    # GDPR
    GDPR_ENABLED: bool = Field(default=True, env="GDPR_ENABLED")
    GDPR_COOKIE_CONSENT: bool = Field(default=True, env="GDPR_COOKIE_CONSENT")
    
    # Stripe
    STRIPE_SECRET_KEY: str = Field(default="", env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
CONFIG
    
    log_success "config.py vytvorený"
}

# Vytvorenie databázového súboru
create_database() {
    log_info "Vytváram databázový súbor..."
    
    cat > backend/app/core/database.py << 'DATABASE'
"""Databázová vrstva."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Asynchrónny engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Asynchrónna session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base pre modely
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Získanie databázovej session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
DATABASE
    
    log_success "database.py vytvorený"
}

# Vytvorenie logging súboru
create_logging() {
    log_info "Vytváram logging súbor..."
    
    cat > backend/app/core/logging.py << 'LOGGING'
"""Logovacia konfigurácia."""

import logging
import sys
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """Nastavenie logovania."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Odstránenie existujúcich handlerov
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler pre konzolu
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # Formát pre JSON logy v produkcii, inak čitateľný formát
    if settings.ENVIRONMENT == "production":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            json_ensure_ascii=False,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Nastavenie logovania pre knižnice
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized with level: {settings.LOG_LEVEL}")
LOGGING
    
    log_success "logging.py vytvorený"
}

# Vytvorenie metrics súboru
create_metrics() {
    log_info "Vytváram metrics súbor..."
    
    cat > backend/app/core/metrics.py << 'METRICS'
"""Monitoring a metriky."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

# Metriky
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Active HTTP requests",
)

DATABASE_CONNECTIONS = Gauge(
    "database_connections",
    "Database connections",
)

REDIS_CONNECTIONS = Gauge(
    "redis_connections",
    "Redis connections",
)


def setup_metrics() -> None:
    """Inicializácia metrík."""
    # Registrácia metrík
    pass


async def metrics_middleware(request: Request, call_next):
    """Middleware pre zber metrík."""
    start_time = time.time()
    
    # Zvýšenie aktívnych požiadaviek
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Zaznamenanie metriky
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status_code,
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(time.time() - start_time)
        
        return response
        
    finally:
        # Zníženie aktívnych požiadaviek
        ACTIVE_REQUESTS.dec()


async def metrics_endpoint(request: Request) -> Response:
    """Endpoint pre metriky."""
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )
METRICS
    
    log_success "metrics.py vytvorený"
}

# Vytvorenie základného modelu
create_base_model() {
    log_info "Vytváram base model..."
    
    cat > backend/app/models/base.py << 'BASE'
"""Základné databázové modely."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
import uuid

from app.core.database import Base


class BaseModel(Base):
    """Základný model so spoločnými stĺpcami."""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    is_active = Column(
        String,
        default=True,
        nullable=False,
        index=True,
    )
    
    @declared_attr
    def __tablename__(cls):
        """Generovanie názvu tabuľky z názvu triedy."""
        return cls.__name__.lower()
    
    def dict(self) -> dict:
        """Konverzia modelu na slovník."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
BASE
    
    log_success "base.py vytvorený"
}

# Hlavná funkcia
main() {
    log_info "Začína stabilizácia projektu..."
    
    check_environment
    create_project_structure
    init_git
    create_gitignore
    create_requirements
    create_pyproject
    create_docker_files
    create_docker_compose
    create_env_template
    create_main_py
    create_api_router
    create_config
    create_database
    create_logging
    create_metrics
    create_base_model
    install_dependencies
    
    log_success "Stabilizácia projektu dokončená"
    log_info "Ďalšie kroky:"
    echo "1. Nakopíruj .env.example na .env a doplň hodnoty"
    echo "2. Spusti docker-compose up -d"
    echo "3. Over backend na http://localhost:8000/docs"
}

# Spustenie
main "$@"
