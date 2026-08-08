from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models.base import AdminLog
from app.shared.repositories.base_repository import BaseRepository

class AdminRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(AdminLog, db)
    
    def get_by_admin_id(self, admin_id: int) -> List[AdminLog]:
        return self.db.query(AdminLog).filter(AdminLog.admin_id == admin_id).all()
    
    def get_by_action(self, action: str) -> List[AdminLog]:
        return self.db.query(AdminLog).filter(AdminLog.action == action).all()
