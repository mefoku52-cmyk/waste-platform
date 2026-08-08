from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.shared.repositories.admin_repository import AdminRepository
from app.shared.models.base import AdminLog

class AdminService:
    def __init__(self, db: Session):
        self.repository = AdminRepository(db)
        self.db = db
    
    def get_all(self) -> List[Dict[str, Any]]:
        items = self.repository.get_all()
        return [self._to_dict(item) for item in items]
    
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        item = self.repository.get_by_id(id)
        if not item:
            return None
        return self._to_dict(item)
    
    def create(self, data: Dict[str, Any], admin_id: int) -> Dict[str, Any]:
        data["admin_id"] = admin_id
        item = self.repository.create(data)
        return self._to_dict(item)
    
    def delete(self, id: int) -> bool:
        return self.repository.delete(id)
    
    def _to_dict(self, item: AdminLog) -> Dict[str, Any]:
        return {
            "id": item.id,
            "admin_id": item.admin_id,
            "action": item.action,
            "target_type": item.target_type,
            "target_id": item.target_id,
            "details": item.details,
            "ip_address": item.ip_address,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }
