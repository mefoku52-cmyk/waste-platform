"""listings repository implementations."""

from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import ListingsEntity
from ..domain.repositories import ListingsRepository
from .mappers import to_domain, to_model
from .models import ListingsModel


class ListingsRepositoryImpl(ListingsRepository):
    """Listings repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> Optional[ListingsEntity]:
        result = await self.session.execute(
            select(ListingsModel).where(ListingsModel.id == id)
        )
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20, company_ids=None) -> list[ListingsEntity]:
        offset = (page - 1) * limit
        stmt = select(ListingsModel)
        if company_ids is not None:
            ids = [str(x) for x in company_ids]
            if not ids:
                return []
            stmt = stmt.where(ListingsModel.company_id.in_(ids))
        stmt = stmt.order_by(ListingsModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self, company_ids=None) -> int:
        stmt = select(func.count()).select_from(ListingsModel)
        if company_ids is not None:
            ids = [str(x) for x in company_ids]
            if not ids:
                return 0
            stmt = stmt.where(ListingsModel.company_id.in_(ids))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_marketplace(self, page: int = 1, limit: int = 20, exclude_company_ids=None) -> list[ListingsEntity]:
        offset = (page - 1) * limit
        stmt = select(ListingsModel).where(ListingsModel.status == "published")
        if exclude_company_ids:
            ids = [str(x) for x in exclude_company_ids if x is not None]
            if ids:
                stmt = stmt.where(ListingsModel.company_id.notin_(ids))
        stmt = stmt.order_by(ListingsModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_marketplace(self, exclude_company_ids=None) -> int:
        stmt = select(func.count()).select_from(ListingsModel).where(ListingsModel.status == "published")
        if exclude_company_ids:
            ids = [str(x) for x in exclude_company_ids if x is not None]
            if ids:
                stmt = stmt.where(ListingsModel.company_id.notin_(ids))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())


    async def get_company_status(self, company_id) -> str | None:
        from sqlalchemy import text
        if company_id is None:
            return None
        result = await self.session.execute(
            text("SELECT status FROM companies WHERE id = :id"),
            {"id": str(company_id)},
        )
        row = result.first()
        return row[0] if row else None

    async def create(self, entity: ListingsEntity) -> ListingsEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: ListingsEntity) -> ListingsEntity:
        model = await self.session.get(ListingsModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.title = entity.title
        model.material_type = entity.material_type
        model.quantity = entity.quantity
        model.unit = entity.unit
        model.price = entity.price
        model.currency = entity.currency
        model.condition = entity.condition
        model.location = entity.location
        model.status = entity.status.value
        model.description = entity.description
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(
            sql_delete(ListingsModel).where(ListingsModel.id == id)
        )
        await self.session.commit()

    async def find_matches(self, *, material_type: str, exclude_company_ids, limit: int = 20):
        """Published listings with same material_type, excluding given companies."""
        stmt = select(ListingsModel).where(ListingsModel.status == "published")
        if material_type:
            stmt = stmt.where(ListingsModel.material_type.ilike(f"%{material_type.strip()}%"))
        if exclude_company_ids:
            stmt = stmt.where(~ListingsModel.company_id.in_(list(exclude_company_ids)))
        stmt = stmt.order_by(ListingsModel.created_at.desc()).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(r) for r in rows]

