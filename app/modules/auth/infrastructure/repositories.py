# TODO: nedokonceny repo - chybaju metody get_active_by_user_id a revoke_family,
#       mapper pouziva nespravne atributy (family_id vs token_family_id).
#       Refresh flow ide cez JWT+Redis, tento repo sa nikde nepouziva.
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.domain.repositories import RefreshSessionRepository
from app.modules.auth.infrastructure.mappers import to_entity
from app.modules.auth.infrastructure.models import RefreshSessionModel


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
        model.updated_at = datetime.now()
        await self._session.flush()

    async def get_by_jti(self, jti: str) -> RefreshSession | None:
        result = await self._session.execute(
            select(RefreshSessionModel).where(RefreshSessionModel.jti == jti)
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None
