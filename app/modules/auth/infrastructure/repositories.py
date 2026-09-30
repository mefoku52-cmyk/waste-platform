from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.domain.repositories import RefreshSessionRepository
from app.modules.auth.infrastructure.mappers import to_entity
from app.modules.auth.infrastructure.models import RefreshSessionModel


class PostgresRefreshSessionRepository(RefreshSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session: RefreshSession) -> None:
        self._session.add(
            RefreshSessionModel(
                id=str(session.id),
                user_id=str(session.user_id),
                token_family_id=session.family_id,
                refresh_token_jti=session.jti,
                refresh_token_hash="unused",
                expires_at=session.expires_at,
                revoked_at=session.revoked_at,
                reuse_detected_at=session.reuse_detected_at,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
        )

    async def update(self, session: RefreshSession) -> None:
        model = (
            await self._session.execute(
                select(RefreshSessionModel).where(
                    RefreshSessionModel.refresh_token_jti == session.jti
                )
            )
        ).scalar_one()
        model.revoked_at = session.revoked_at
        model.reuse_detected_at = session.reuse_detected_at
        model.updated_at = datetime.now()
        await self._session.flush()

    async def get_by_jti(self, jti: str):
        model = (
            await self._session.execute(
                select(RefreshSessionModel).where(RefreshSessionModel.refresh_token_jti == jti)
            )
        ).scalar_one_or_none()
        return to_entity(model) if model else None

    async def get_active_by_user_id(self, user_id: UUID):
        rows = (
            (
                await self._session.execute(
                    select(RefreshSessionModel).where(
                        RefreshSessionModel.user_id == str(user_id),
                        RefreshSessionModel.revoked_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        return [to_entity(m) for m in rows]

    async def revoke_family(self, family_id: str, revoked_at) -> None:
        await self._session.execute(
            update(RefreshSessionModel)
            .where(RefreshSessionModel.token_family_id == family_id)
            .values(revoked_at=revoked_at, updated_at=revoked_at)
        )
        await self._session.flush()
