from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.shared.repositories.listing_repository import ListingRepository
from app.shared.models.base import Listing

class ListingService:
    def __init__(self, db: Session):
        self.repository = ListingRepository(db)
        self.db = db
    
    def get_all(self, user_id: Optional[int] = None, role: str = "user") -> List[Dict[str, Any]]:
        if role == "admin":
            items = self.repository.get_all()
        elif user_id:
            items = self.repository.get_by_user_id(user_id)
        else:
            items = []
        return [self._to_dict(item) for item in items]
    
    def get_by_id(self, id: int, user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        item = self.repository.get_by_id(id)
        if not item:
            return None
        if role != "admin" and item.user_id != user_id:
            return None
        return self._to_dict(item)
    
    def create(self, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        data["user_id"] = user_id
        item = self.repository.create(data)
        return self._to_dict(item)
    
    def update(self, id: int, data: Dict[str, Any], user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        item = self.repository.get_by_id(id)
        if not item:
            return None
        if role != "admin" and item.user_id != user_id:
            return None
        updated = self.repository.update(id, data)
        return self._to_dict(updated) if updated else None
    
    def delete(self, id: int, user_id: Optional[int] = None, role: str = "user") -> bool:
        item = self.repository.get_by_id(id)
        if not item:
            return False
        if role != "admin" and item.user_id != user_id:
            return False
        return self.repository.delete(id)
    
    def _to_dict(self, item: Listing) -> Dict[str, Any]:
        return {
            "id": item.id,
            "user_id": item.user_id,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "price": item.price,
            "currency": item.currency,
            "status": item.status,
            "location": item.location,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }
