from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models.base import Notification
from app.shared.repositories.base_repository import BaseRepository

class NotificationRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Notification, db)
    
    def get_by_user_id(self, user_id: int) -> List[Notification]:
        return self.db.query(Notification).filter(Notification.user_id == user_id).all()
    
    def get_unread_by_user_id(self, user_id: int) -> List[Notification]:
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).all()
