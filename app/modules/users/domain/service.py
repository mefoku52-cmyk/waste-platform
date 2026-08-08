from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.shared.repositories.user_repository import UserRepository
from app.shared.models.base import User

class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.db = db
    
    def get_all(self, role: str = "user") -> List[Dict[str, Any]]:
        if role == "admin":
            users = self.repository.get_all()
        else:
            # Bežný používateľ vidí len svoj profil
            return []
        return [self._to_dict(user) for user in users]
    
    def get_by_id(self, id: int, current_user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        user = self.repository.get_by_id(id)
        if not user:
            return None
        # Admin vidí všetkých, bežný používateľ len seba
        if role != "admin" and user.id != current_user_id:
            return None
        return self._to_dict(user)
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        user = self.repository.get_by_email(email)
        if not user:
            return None
        return self._to_dict(user)
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user = self.repository.create(data)
        return self._to_dict(user)
    
    def update(self, id: int, data: Dict[str, Any], current_user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        user = self.repository.get_by_id(id)
        if not user:
            return None
        if role != "admin" and user.id != current_user_id:
            return None
        updated = self.repository.update(id, data)
        return self._to_dict(updated) if updated else None
    
    def delete(self, id: int, current_user_id: Optional[int] = None, role: str = "user") -> bool:
        user = self.repository.get_by_id(id)
        if not user:
            return False
        if role != "admin" and user.id != current_user_id:
            return False
        return self.repository.delete(id)
    
    def _to_dict(self, user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "permissions": user.permissions.split(",") if user.permissions else [],
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
