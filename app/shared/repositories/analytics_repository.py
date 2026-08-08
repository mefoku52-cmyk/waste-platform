from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models.base import Analytics
from app.shared.repositories.base_repository import BaseRepository

class AnalyticsRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Analytics, db)
    
    def get_by_user_id(self, user_id: int) -> List[Analytics]:
        return self.db.query(Analytics).filter(Analytics.user_id == user_id).all()
    
    def get_by_event_type(self, event_type: str) -> List[Analytics]:
        return self.db.query(Analytics).filter(Analytics.event_type == event_type).all()
