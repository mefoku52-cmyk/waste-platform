"""listings repository implementations."""

import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import ListingsEntity
from ..domain.repositories import ListingsRepository
from .mappers import to_domain, to_model
from .models import ListingsModel


def _uuid(value):
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class ListingsRepositoryImpl(ListingsRepository):
    """Listings repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> ListingsEntity | None:
        result = await self.session.execute(select(ListingsModel).where(ListingsModel.id == _uuid(id)))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(
        self, page: int = 1, limit: int = 20, company_ids=None
    ) -> list[ListingsEntity]:
        offset = (page - 1) * limit
        stmt = select(ListingsModel)
        if company_ids is not None:
            ids = [_uuid(x) for x in company_ids]
            if not ids:
                return []
            stmt = stmt.where(ListingsModel.company_id.in_(ids))
        from sqlalchemy import case

        stmt = (
            stmt.order_by(
                case((ListingsModel.promoted_until > func.now(), 0), else_=1),
                ListingsModel.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self, company_ids=None) -> int:
        stmt = select(func.count()).select_from(ListingsModel)
        if company_ids is not None:
            ids = [_uuid(x) for x in company_ids]
            if not ids:
                return 0
            stmt = stmt.where(ListingsModel.company_id.in_(ids))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    @staticmethod
    def _apply_marketplace_filters(
        stmt,
        *,
        exclude_company_ids=None,
        q: str | None = None,
        material_type: str | None = None,
        location: str | None = None,
    ):
        from sqlalchemy import func, or_

        if exclude_company_ids:
            ids = [_uuid(x) for x in exclude_company_ids if x is not None]
            if ids:
                stmt = stmt.where(ListingsModel.company_id.notin_(ids))
        if material_type:
            mt = str(material_type).strip()
            if mt:
                stmt = stmt.where(func.lower(ListingsModel.material_type) == func.lower(mt))
        if location:
            loc = str(location).strip()
            if loc:
                stmt = stmt.where(func.lower(ListingsModel.location).contains(func.lower(loc)))
        if q:
            qq = str(q).strip()
            if qq:
                pattern = f"%{qq.lower()}%"
                stmt = stmt.where(
                    or_(
                        func.lower(ListingsModel.title).contains(pattern),
                        func.lower(ListingsModel.description).contains(pattern),
                        func.lower(ListingsModel.material_type).contains(pattern),
                        func.lower(ListingsModel.location).contains(pattern),
                    )
                )
        return stmt

    async def list_marketplace(
        self,
        page: int = 1,
        limit: int = 20,
        exclude_company_ids=None,
        *,
        q: str | None = None,
        material_type: str | None = None,
        location: str | None = None,
    ) -> list[ListingsEntity]:
        offset = (page - 1) * limit
        stmt = select(ListingsModel).where(ListingsModel.status == "published")
        stmt = self._apply_marketplace_filters(
            stmt,
            exclude_company_ids=exclude_company_ids,
            q=q,
            material_type=material_type,
            location=location,
        )
        # promoted (TOP) listings first, then by created_at
        from sqlalchemy import case

        stmt = (
            stmt.order_by(
                case((ListingsModel.promoted_until > func.now(), 0), else_=1),
                ListingsModel.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_marketplace(
        self,
        exclude_company_ids=None,
        *,
        q: str | None = None,
        material_type: str | None = None,
        location: str | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ListingsModel)
            .where(ListingsModel.status == "published")
        )
        stmt = self._apply_marketplace_filters(
            stmt,
            exclude_company_ids=exclude_company_ids,
            q=q,
            material_type=material_type,
            location=location,
        )
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
        await self.session.execute(sql_delete(ListingsModel).where(ListingsModel.id == _uuid(id)))
        await self.session.commit()

    async def find_matches(self, *, material_type: str, exclude_company_ids, limit: int = 20):
        """Published listings with same material_type, excluding given companies."""
        stmt = select(ListingsModel).where(ListingsModel.status == "published")
        if material_type:
            stmt = stmt.where(ListingsModel.material_type.ilike(f"%{material_type.strip()}%"))
        if exclude_company_ids:
            stmt = stmt.where(~ListingsModel.company_id.in_([_uuid(x) for x in exclude_company_ids]))
        stmt = stmt.order_by(ListingsModel.created_at.desc()).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(r) for r in rows]

    async def record_view(self, listing_id, user_id) -> None:
        import uuid as _uuid
        from datetime import datetime

        from .models import ListingViewModel

        lid = listing_id if isinstance(listing_id, _uuid.UUID) else _uuid.UUID(str(listing_id))
        uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
        v = ListingViewModel(listing_id=lid, user_id=uid, viewed_at=datetime.now())
        self.session.add(v)
        await self.session.commit()

    async def promote(self, listing_id: str, *, days: int, tier: str) -> None:
        """Set promoted_until = now + days, promoted_tier = tier."""
        from datetime import datetime, timedelta
        from uuid import UUID as _UUID

        lid = listing_id if isinstance(listing_id, _UUID) else _UUID(str(listing_id))
        model = await self.session.get(ListingsModel, lid)
        if model is None:
            raise ValueError("Listing not found")
        model.promoted_until = datetime.now() + timedelta(days=days)
        model.promoted_tier = tier
        model.updated_at = datetime.now()
        await self.session.commit()

    async def unpromote(self, listing_id: str) -> None:
        """Clear promotion."""
        from datetime import datetime
        from uuid import UUID as _UUID

        lid = listing_id if isinstance(listing_id, _UUID) else _UUID(str(listing_id))
        model = await self.session.get(ListingsModel, lid)
        if model is None:
            raise ValueError("Listing not found")
        model.promoted_until = None
        model.promoted_tier = None
        model.updated_at = datetime.now()
        await self.session.commit()

    async def get_listing_stats(self, listing_id) -> dict:
        import uuid as _uuid

        from .models import ListingViewModel

        lid = listing_id if isinstance(listing_id, _uuid.UUID) else _uuid.UUID(str(listing_id))
        total = await self.session.execute(
            select(func.count())
            .select_from(ListingViewModel)
            .where(ListingViewModel.listing_id == lid)
        )
        unique = await self.session.execute(
            select(func.count(func.distinct(ListingViewModel.user_id))).where(
                ListingViewModel.listing_id == lid
            )
        )
        return {"views": int(total.scalar_one()), "unique_viewers": int(unique.scalar_one())}
