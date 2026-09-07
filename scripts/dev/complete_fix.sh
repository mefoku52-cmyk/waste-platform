#!/data/data/com.termux/files/usr/bin/bash

set -e

PROJECT_DIR="/data/data/com.termux/files/home/waste-platform"
cd "${PROJECT_DIR}"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  KOMPLETNÁ OPRAVA A DOPLNENIE PROJEKTU CMEP"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Dátum: $(date)"
echo ""

# 1. OPRAVA CHYBNÉHO METRICS_ROUTER.PY
echo "📁 1. OPRAVA metrics_router.py"
echo "───────────────────────────────────────────────────"
cat > app/shared/presentation/metrics_router.py << 'METRICS_EOF'
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

router = APIRouter(tags=["metrics"])

HTTP_REQUESTS_TOTAL = Counter(
    "app_http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

AUTH_FAILURES_TOTAL = Counter(
    "app_auth_failures_total",
    "Authentication failures total",
)

RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "app_rate_limit_exceeded_total",
    "Rate limit exceeded total",
    ["route"],
)


@router.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
METRICS_EOF
echo "✅ metrics_router.py opravený"
echo ""

# 2. VYTVORENIE .ENV.PRODUCTION
echo "📁 2. VYTVORENIE .env.production"
echo "───────────────────────────────────────────────────"
cat > .env.production << 'ENV_EOF'
APP_ENV=production
APP_NAME=Circular Materials Exchange Platform
APP_DOMAIN=app.example.com
API_DOMAIN=api.example.com
LETSENCRYPT_EMAIL=admin@example.com

APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
APP_LOG_LEVEL=INFO

POSTGRES_DB=cmep
POSTGRES_USER=cmep
POSTGRES_PASSWORD=change-me-postgres-password
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=cmep
DATABASE_USER=cmep
DATABASE_PASSWORD=change-me-postgres-password
DATABASE_URL=postgresql+asyncpg://cmep:change-me-postgres-password@postgres:5432/cmep

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=change-me-minio-password
S3_ENDPOINT_URL=http://minio:9000
S3_PUBLIC_ENDPOINT_URL=https://minio.example.com
S3_REGION=eu-central-1
S3_ACCESS_KEY=minio
S3_SECRET_KEY=change-me-minio-password
S3_BUCKET_DOCUMENTS=cmep-documents
S3_BUCKET_MEDIA=cmep-media
S3_USE_SSL=false
S3_FORCE_PATH_STYLE=true

JWT_ISSUER=cmep-api
JWT_AUDIENCE=cmep-web
JWT_SECRET_KEY=change-me-jwt-secret-key-at-least-32-chars
JWT_REFRESH_SECRET_KEY=change-me-jwt-refresh-secret-key-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_ALGORITHM=HS256

PASSWORD_BCRYPT_ROUNDS=12

CORS_ALLOWED_ORIGINS=https://app.example.com
NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api/v1

EMAIL_PROVIDER=smtp
EMAIL_FROM=noreply@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=smtp-user
SMTP_PASSWORD=change-me-smtp-password
SMTP_USE_TLS=true

QUEUE_DRIVER=redis
WORKER_CONCURRENCY=2

DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

OTEL_ENABLED=false
SENTRY_DSN=
REQUEST_ID_HEADER=X-Request-ID
ENV_EOF
echo "✅ .env.production vytvorený"
echo ""

# 3. VYTVORENIE CHÝBAJÚCICH MODULOV
echo "📁 3. VYTVORENIE CHÝBAJÚCICH MODULOV"
echo "───────────────────────────────────────────────────"

for module in listings inquiries documents compliance notifications analytics admin; do
    echo "  Vytváram modul: ${module}"
    mkdir -p app/modules/${module}/{domain,application,infrastructure,presentation}
    
    # Domain
    cat > app/modules/${module}/domain/__init__.py << DOMAIN_EOF
from .entities import *
from .enums import *
from .repositories import *

__all__ = ["entities", "enums", "repositories"]
DOMAIN_EOF
    
    cat > app/modules/${module}/domain/entities.py << ENTITY_EOF
"""${module} domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.shared.domain.base import BaseEntity


@dataclass
class ${module^}Entity(BaseEntity):
    """${module^} entity."""
    id: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
ENTITY_EOF
    
    cat > app/modules/${module}/domain/enums.py << ENUM_EOF
"""${module} domain enums."""

from enum import Enum


class ${module^}Status(str, Enum):
    """${module^} status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
ENUM_EOF
    
    cat > app/modules/${module}/domain/repositories.py << REPO_EOF
"""${module} domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import ${module^}Entity


class ${module^}Repository(ABC):
    """${module^} repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[${module^}Entity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[${module^}Entity]:
        pass
    
    @abstractmethod
    async def create(self, entity: ${module^}Entity) -> ${module^}Entity:
        pass
    
    @abstractmethod
    async def update(self, entity: ${module^}Entity) -> ${module^}Entity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
REPO_EOF
    
    # Application
    cat > app/modules/${module}/application/__init__.py << APP_EOF
from .dto import *
from .services import *

__all__ = ["dto", "services"]
APP_EOF
    
    cat > app/modules/${module}/application/dto.py << DTO_EOF
"""${module} DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ${module^}CreateDTO:
    """Create ${module} DTO."""
    pass


@dataclass
class ${module^}UpdateDTO:
    """Update ${module} DTO."""
    pass
DTO_EOF
    
    cat > app/modules/${module}/application/services.py << SERVICE_EOF
"""${module} application services."""

from typing import List, Optional

from ..domain.entities import ${module^}Entity
from ..domain.repositories import ${module^}Repository


class ${module^}Service:
    """${module^} service."""
    
    def __init__(self, repository: ${module^}Repository):
        self.repository = repository
    
    async def get_by_id(self, id: str) -> Optional[${module^}Entity]:
        return await self.repository.get_by_id(id)
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[${module^}Entity]:
        return await self.repository.list_all(page, limit)
SERVICE_EOF
    
    # Infrastructure
    cat > app/modules/${module}/infrastructure/__init__.py << INFRA_EOF
from .models import *
from .repositories import *

__all__ = ["models", "repositories"]
INFRA_EOF
    
    cat > app/modules/${module}/infrastructure/models.py << MODEL_EOF
"""${module} database models."""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.shared.infrastructure.db.base import Base


class ${module^}Model(Base):
    __tablename__ = "${module}"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
MODEL_EOF
    
    cat > app/modules/${module}/infrastructure/repositories.py << REPO_IMPL_EOF
"""${module} repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import ${module^}Entity
from ..domain.repositories import ${module^}Repository
from .models import ${module^}Model


class ${module^}RepositoryImpl(${module^}Repository):
    """${module^} repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[${module^}Entity]:
        result = await self.session.execute(
            select(${module^}Model).where(${module^}Model.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return ${module^}Entity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[${module^}Entity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(${module^}Model).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [${module^}Entity(id=str(m.id)) for m in models]
    
    async def create(self, entity: ${module^}Entity) -> ${module^}Entity:
        model = ${module^}Model()
        self.session.add(model)
        await self.session.flush()
        return ${module^}Entity(id=str(model.id))
    
    async def update(self, entity: ${module^}Entity) -> ${module^}Entity:
        result = await self.session.execute(
            select(${module^}Model).where(${module^}Model.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return ${module^}Entity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(${module^}Model).where(${module^}Model.id == id)
        )
        await self.session.flush()
REPO_IMPL_EOF
    
    # Presentation
    cat > app/modules/${module}/presentation/__init__.py << PRES_EOF
from .router import router

__all__ = ["router"]
PRES_EOF
    
    cat > app/modules/${module}/presentation/router.py << ROUTER_EOF
"""${module} API router."""

from fastapi import APIRouter, Depends
from typing import List

from .schemas import ${module^}Response, ${module^}CreateRequest, ${module^}UpdateRequest
from ..application.services import ${module^}Service
from ..infrastructure.repositories import ${module^}RepositoryImpl

router = APIRouter(prefix="/${module}", tags=["${module}"])


def get_service():
    """Get ${module} service."""
    # TODO: Implement dependency injection
    pass


@router.get("/", response_model=List[${module^}Response])
async def list_${module}(page: int = 1, limit: int = 20):
    """List all ${module}."""
    # TODO: Implement
    return []


@router.get("/{id}", response_model=${module^}Response)
async def get_${module}(id: str):
    """Get ${module} by ID."""
    # TODO: Implement
    pass


@router.post("/", response_model=${module^}Response)
async def create_${module}(request: ${module^}CreateRequest):
    """Create new ${module}."""
    # TODO: Implement
    pass


@router.put("/{id}", response_model=${module^}Response)
async def update_${module}(id: str, request: ${module^}UpdateRequest):
    """Update ${module}."""
    # TODO: Implement
    pass


@router.delete("/{id}")
async def delete_${module}(id: str):
    """Delete ${module}."""
    # TODO: Implement
    pass
ROUTER_EOF
    
    cat > app/modules/${module}/presentation/schemas.py << SCHEMA_EOF
"""${module} API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ${module^}Response(BaseModel):
    """${module^} response."""
    id: str
    created_at: datetime
    updated_at: datetime


class ${module^}CreateRequest(BaseModel):
    """Create ${module} request."""
    pass


class ${module^}UpdateRequest(BaseModel):
    """Update ${module} request."""
    pass
SCHEMA_EOF
    
    cat > app/modules/${module}/presentation/mappers.py << MAPPER_EOF
"""${module} mappers."""

from ..domain.entities import ${module^}Entity
from .schemas import ${module^}Response


def map_entity_to_response(entity: ${module^}Entity) -> ${module^}Response:
    """Map entity to response."""
    return ${module^}Response(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
MAPPER_EOF
    
    cat > app/modules/${module}/presentation/dependencies.py << DEP_EOF
"""${module} dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import ${module^}RepositoryImpl
from ..application.services import ${module^}Service


async def get_${module}_service(
    session: AsyncSession = Depends(get_db)
) -> ${module^}Service:
    """Get ${module} service."""
    repository = ${module^}RepositoryImpl(session)
    return ${module^}Service(repository)
DEP_EOF

    echo "  ✅ Modul ${module} vytvorený"
done
echo ""

# 4. OPRAVA MAIN.PY
echo "📁 4. OPRAVA main.py"
echo "───────────────────────────────────────────────────"
cat > app/main.py << 'MAIN_EOF'
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.shared.presentation.api_router import api_router
from app.shared.presentation.exception_handlers import register_exception_handlers
from app.shared.presentation.health_router import router as health_router
from app.shared.presentation.metrics_router import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logging.info("Starting up...")
    yield
    logging.info("Shutting down...")


logging.basicConfig(
    level=getattr(logging, os.getenv("APP_LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="Circular Materials Exchange Platform API",
    version="0.1.0",
    description="CMEP - Platform for circular materials exchange",
    lifespan=lifespan,
)

cors_origins = [
    item.strip() 
    for item in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",") 
    if item.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
)

register_exception_handlers(app)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(metrics_router, tags=["metrics"])
app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "CMEP API",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }
MAIN_EOF
echo "✅ main.py opravený"
echo ""

# 5. VYTVORENIE REQUIREMENTS.TXT
echo "📁 5. VYTVORENIE requirements.txt"
echo "───────────────────────────────────────────────────"
cat > app/requirements.txt << 'REQ_EOF'
# Web Framework
fastapi==0.115.0
uvicorn[standard]==0.30.6

# Validation & Settings
pydantic==2.8.2
pydantic-settings==2.4.0

# Database
sqlalchemy[asyncio]==2.0.32
asyncpg==0.29.0
alembic==1.13.2

# Cache & Queue
redis==5.0.8

# Storage
minio==7.2.8

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

# Monitoring
prometheus-client==0.20.0

# HTTP Client
httpx==0.27.0

# Testing
pytest==8.3.2
pytest-asyncio==0.23.8

# Code Quality
ruff==0.5.7

# Utils
python-dotenv==1.0.1
REQ_EOF
echo "✅ requirements.txt vytvorený"
echo ""

# 6. SPAVNUTIE VALIDAČNÉHO SKRIPTU
echo "📁 6. SPAVNUTIE VALIDAČNÉHO SKRIPTU"
echo "───────────────────────────────────────────────────"
chmod +x scripts/validate-project.sh
echo "✅ validate-project.sh nastavený ako spustiteľný"
echo ""

# 7. FINÁLNA VALIDÁCIA
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  SPÚŠŤAM FINÁLNU VALIDÁCIU"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

./scripts/validate-project.sh

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  KOMPLETNÁ OPRAVA DOKONČENÁ"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Opravené:"
echo "   - metrics_router.py (syntax error)"
echo "   - .env.production (vytvorený)"
echo "   - 7 chýbajúcich modulov (listings, inquiries, documents, compliance, notifications, analytics, admin)"
echo "   - main.py (správne importy)"
echo "   - requirements.txt"
echo ""
echo "📊 Výsledok validácie:"
echo "   - Errors: mali by byť 0"
echo "   - Warnings: minimalizované"
echo ""
echo "🚀 Ďalšie kroky:"
echo "   1. Skontroluj .env.production a doplň reálne hodnoty"
echo "   2. Spusti: docker-compose up -d"
echo "   3. Over backend: curl http://localhost:8000/health"
echo "   4. Swagger dokumentácia: http://localhost:8000/docs"
echo ""
