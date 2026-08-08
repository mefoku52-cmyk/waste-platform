from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.shared.repositories.inquiry_repository import InquiryRepository
from app.shared.models.base import Inquiry

class InquiryService:
    """Servisná vrstva pre inquiries - používa databázu"""
    
    def __init__(self, db: Session):
        self.repository = InquiryRepository(db)
        self.db = db
    
    def get_all(self, user_id: Optional[int] = None, role: str = "user") -> List[Dict[str, Any]]:
        """Získa všetky inquiries - admin vidí všetky, user len svoje"""
        if role == "admin":
            inquiries = self.repository.get_all()
        elif user_id:
            inquiries = self.repository.get_by_user_id(user_id)
        else:
            inquiries = []
        return [self._to_dict(inquiry) for inquiry in inquiries]
    
    def get_by_id(self, id: int, user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        """Získa inquiry podľa ID - kontrola prístupu"""
        inquiry = self.repository.get_by_id(id)
        if not inquiry:
            return None
        # Kontrola prístupu
        if role != "admin" and inquiry.user_id != user_id:
            return None
        return self._to_dict(inquiry)
    
    def create(self, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Vytvorí nové inquiry"""
        data["user_id"] = user_id
        inquiry = self.repository.create(data)
        return self._to_dict(inquiry)
    
    def update(self, id: int, data: Dict[str, Any], user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        """Aktualizuje inquiry - kontrola prístupu"""
        inquiry = self.repository.get_by_id(id)
        if not inquiry:
            return None
        # Kontrola prístupu
        if role != "admin" and inquiry.user_id != user_id:
            return None
        updated = self.repository.update(id, data)
        return self._to_dict(updated) if updated else None
    
    def delete(self, id: int, user_id: Optional[int] = None, role: str = "user") -> bool:
        """Vymaže inquiry - kontrola prístupu"""
        inquiry = self.repository.get_by_id(id)
        if not inquiry:
            return False
        # Kontrola prístupu
        if role != "admin" and inquiry.user_id != user_id:
            return False
        return self.repository.delete(id)
    
    def _to_dict(self, inquiry: Inquiry) -> Dict[str, Any]:
        """Konvertuje model na dict"""
        return {
            "id": inquiry.id,
            "user_id": inquiry.user_id,
            "name": inquiry.name,
            "description": inquiry.description,
            "status": inquiry.status,
            "created_at": inquiry.created_at.isoformat() if inquiry.created_at else None,
            "updated_at": inquiry.updated_at.isoformat() if inquiry.updated_at else None
        }
