from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.domain.repositories import RefreshSessionRepository
from app.modules.auth.infrastructure.mappers import to_domain, to_model
from app.modules.auth.infrastructure.models import RefreshSessionModel


class SqlAlchemyRefreshSessionRepository(RefreshSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, session_entity: RefreshSession) -> None:
        self.session.add(to_model(session_entity))
        await self.session.commit()

    async def get_by_jti(self, jti: str) -> RefreshSession | None:
        stmt = select(RefreshSessionModel).where(RefreshSessionModel.refresh_token_jti == jti)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_active_by_user_id(self, user_id: UUID) -> list[RefreshSession]:
        stmt = select(RefreshSessionModel).where(
            RefreshSessionModel.user_id == str(user_id),
            RefreshSessionModel.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return [to_domain(item) for item in result.scalars().all()]

    async def update(self, session_entity: RefreshSession) -> None:
        model = await self.session.get(RefreshSessionModel, str(session_entity.id))
        if model is None:
            return
        model.revoked_at = session_entity.revoked_at
        model.replaced_by_jti = session_entity.replaced_by_jti
        model.reuse_detected_at = session_entity.reuse_detected_at
        model.updated_at = session_entity.updated_at
        model.updated_by_user_id = str(session_entity.updated_by_user_id) if session_entity.updated_by_user_id else None
        await self.session.commit()

    async def revoke_family(self, family_id: str, revoked_at) -> None:
        stmt = (
            update(RefreshSessionModel)
            .where(RefreshSessionModel.token_family_id == family_id, RefreshSessionModel.revoked_at.is_(None))
            .values(revoked_at=revoked_at, updated_at=revoked_at)
        )
        await self.session.execute(stmt)
        await self.session.commit()
