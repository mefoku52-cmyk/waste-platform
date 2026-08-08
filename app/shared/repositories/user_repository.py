from sqlalchemy.orm import Session
from typing import Optional
from app.shared.models.base import User
from app.shared.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    """Repository pre User model"""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_role(self, role: str):
        return self.db.query(User).filter(User.role == role).all()
