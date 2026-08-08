from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.shared.repositories.analytics_repository import AnalyticsRepository
from app.shared.models.base import Analytics
import json

class AnalyticsService:
    def __init__(self, db: Session):
        self.repository = AnalyticsRepository(db)
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
        # Konvertuj event_data na JSON string ak je dict
        if "event_data" in data and isinstance(data["event_data"], dict):
            data["event_data"] = json.dumps(data["event_data"])
        item = self.repository.create(data)
        return self._to_dict(item)
    
    def delete(self, id: int, user_id: Optional[int] = None, role: str = "user") -> bool:
        item = self.repository.get_by_id(id)
        if not item:
            return False
        if role != "admin" and item.user_id != user_id:
            return False
        return self.repository.delete(id)
    
    def _to_dict(self, item: Analytics) -> Dict[str, Any]:
        event_data = item.event_data
        try:
            event_data = json.loads(event_data) if event_data else None
        except:
            pass
        return {
            "id": item.id,
            "user_id": item.user_id,
            "event_type": item.event_type,
            "event_name": item.event_name,
            "event_data": event_data,
            "ip_address": item.ip_address,
            "user_agent": item.user_agent,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }
