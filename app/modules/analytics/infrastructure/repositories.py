"""analytics repository implementations."""

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import AnalyticsEventEntity
from ..domain.repositories import AnalyticsEventRepository
from .mappers import to_domain, to_model
from .models import AnalyticsEventModel


class AnalyticsEventRepositoryImpl(AnalyticsEventRepository):
    """AnalyticsEvent repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> AnalyticsEventEntity | None:
        result = await self.session.execute(
            select(AnalyticsEventModel).where(AnalyticsEventModel.id == id)
        )
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(
        self, page: int = 1, limit: int = 20, company_ids=None
    ) -> list[AnalyticsEventEntity]:
        offset = (page - 1) * limit
        stmt = select(AnalyticsEventModel)
        if company_ids is not None:
            ids = [str(x) for x in company_ids]
            if not ids:
                return []
            stmt = stmt.where(AnalyticsEventModel.company_id.in_(ids))
        stmt = stmt.order_by(AnalyticsEventModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self, company_ids=None) -> int:
        stmt = select(func.count()).select_from(AnalyticsEventModel)
        if company_ids is not None:
            ids = [str(x) for x in company_ids]
            if not ids:
                return 0
            stmt = stmt.where(AnalyticsEventModel.company_id.in_(ids))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, entity: AnalyticsEventEntity) -> AnalyticsEventEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: AnalyticsEventEntity) -> AnalyticsEventEntity:
        model = await self.session.get(AnalyticsEventModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.event_type = entity.event_type
        model.entity_type = entity.entity_type
        model.entity_id = entity.entity_id
        model.company_id = entity.company_id
        model.event_metadata = entity.event_metadata
        model.recorded_at = entity.recorded_at
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(
            sql_delete(AnalyticsEventModel).where(AnalyticsEventModel.id == id)
        )
        await self.session.commit()
