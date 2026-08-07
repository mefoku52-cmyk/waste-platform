"""User repository."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.repositories.base import BaseRepository
from app.models.user import User, UserStatus
from app.models.company import Company


class UserRepository(BaseRepository[User]):
    """User repository."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(self, email: str, username: str) -> Optional[User]:
        """Get user by email or username."""
        result = await self.session.execute(
            select(User).where(
                or_(User.email == email, User.username == username)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_users(self) -> List[User]:
        """Get all active users."""
        result = await self.session.execute(
            select(User).where(User.status == UserStatus.ACTIVE)
        )
        return result.scalars().all()
    
    async def get_users_by_company(self, company_id: UUID) -> List[User]:
        """Get users by company."""
        result = await self.session.execute(
            select(User).join(User.companies).where(Company.id == company_id)
        )
        return result.scalars().all()
    
    async def update_last_login(self, user_id: UUID, ip_address: str) -> None:
        """Update user last login."""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            user.last_login_ip = ip_address
            await self.session.commit()
