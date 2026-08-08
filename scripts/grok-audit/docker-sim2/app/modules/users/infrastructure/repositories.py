from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.domain.entities import User
from app.modules.users.domain.repositories import UserRepository
from app.modules.users.infrastructure.mappers import to_domain
from app.modules.users.infrastructure.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user: User) -> None:
        from app.modules.users.infrastructure.mappers import to_model
        self.session.add(to_model(user))
        await self.session.commit()

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == str(user_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list(self, *, status: str | None, company_id: UUID | None, q: str | None, page: int, page_size: int) -> tuple[list[User], int]:
        stmt = select(UserModel)
        count_stmt = select(func.count()).select_from(UserModel)

        if status:
            stmt = stmt.where(UserModel.status == status)
            count_stmt = count_stmt.where(UserModel.status == status)

        if q:
            pattern = f"%{q}%"
            filter_expr = or_(
                UserModel.email.ilike(pattern),
                UserModel.first_name.ilike(pattern),
                UserModel.last_name.ilike(pattern),
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        stmt = stmt.order_by(UserModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        rows = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()

        return [to_domain(row) for row in rows], int(total)

    async def update(self, user: User) -> None:
        model = await self.session.get(UserModel, str(user.id))
        if model is None:
            return
        model.status = user.status.value
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.display_name = user.display_name
        model.phone = user.phone
        model.locale = user.locale
        model.timezone = user.timezone
        model.last_login_at = user.last_login_at
        model.updated_at = user.updated_at
        model.updated_by_user_id = str(user.updated_by_user_id) if user.updated_by_user_id else None
        await self.session.commit()
