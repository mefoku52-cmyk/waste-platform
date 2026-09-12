#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "FIX PYRIGHT TYPE ERRORS"
echo "========================================"

cd "$HOME/waste-platform"

# 1. Oprava app/modules/auth/infrastructure/mappers.py
cat > app/modules/auth/infrastructure/mappers.py << 'ENDMAP'
from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.infrastructure.models import RefreshSessionModel
from datetime import timezone

def to_entity(model: RefreshSessionModel) -> RefreshSession:
    return RefreshSession(
        id=model.id,
        user_id=model.user_id,
        family_id=model.family_id,
        jti=model.jti,
        expires_at=model.expires_at.replace(tzinfo=timezone.utc) if model.expires_at else None,
        revoked_at=model.revoked_at.replace(tzinfo=timezone.utc) if model.revoked_at else None,
        reuse_detected_at=model.reuse_detected_at.replace(tzinfo=timezone.utc) if model.reuse_detected_at else None,
        created_at=model.created_at.replace(tzinfo=timezone.utc),
        updated_at=model.updated_at.replace(tzinfo=timezone.utc),
    )
ENDMAP

# 2. Oprava app/modules/auth/infrastructure/repositories.py
cat > app/modules/auth/infrastructure/repositories.py << 'ENDREPO'
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.domain.repositories import RefreshSessionRepository
from app.modules.auth.infrastructure.models import RefreshSessionModel
from app.modules.auth.infrastructure.mappers import to_entity
from datetime import datetime, timezone

class PostgresRefreshSessionRepository(RefreshSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session: RefreshSession) -> None:
        model = RefreshSessionModel(
            id=session.id,
            user_id=session.user_id,
            family_id=session.family_id,
            jti=session.jti,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
            reuse_detected_at=session.reuse_detected_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        self._session.add(model)

    async def update(self, session: RefreshSession) -> None:
        result = await self._session.execute(
            select(RefreshSessionModel).where(RefreshSessionModel.jti == session.jti)
        )
        model = result.scalar_one()
        model.revoked_at = session.revoked_at
        model.reuse_detected_at = session.reuse_detected_at
        model.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def get_by_jti(self, jti: str) -> RefreshSession | None:
        result = await self._session.execute(
            select(RefreshSessionModel).where(RefreshSessionModel.jti == jti)
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None
ENDREPO

# 3. Oprava app/modules/auth/domain/entities.py
cat > app/modules/auth/domain/entities.py << 'ENDENT'
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

@dataclass
class RefreshSession:
    id: UUID
    user_id: UUID
    family_id: str
    jti: str
    expires_at: datetime
    revoked_at: datetime | None = None
    reuse_detected_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
ENDENT

# 4. Oprava app/modules/compliance/infrastructure/models.py
cat > app/modules/compliance/infrastructure/models.py << 'ENDCOMP'
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class ComplianceRecordModel(Base):
    __tablename__ = "compliance_records"
    id = Column(UUID(as_uuid=True), primary_key=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    regulation_type = Column(String)
    document_ref = Column(String)
    valid_until = Column(DateTime)
    notes = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(UUID(as_uuid=True))
    updated_by_user_id = Column(UUID(as_uuid=True))
ENDCOMP

# 5. Oprava app/modules/documents/infrastructure/models.py
cat > app/modules/documents/infrastructure/models.py << 'ENDDOC'
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String)
    document_type = Column(String)
    file_url = Column(String)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    listing_id = Column(UUID(as_uuid=True))
    status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(UUID(as_uuid=True))
    updated_by_user_id = Column(UUID(as_uuid=True))
ENDDOC

echo "========================================"
echo "HOTOVO - hlavne súbory opravené"
echo "Teraz spusti pyright znova"
echo "========================================"
