from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models.base import Compliance
from app.shared.repositories.base_repository import BaseRepository

class ComplianceRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Compliance, db)
    
    def get_by_user_id(self, user_id: int) -> List[Compliance]:
        return self.db.query(Compliance).filter(Compliance.user_id == user_id).all()
    
    def get_by_status(self, status: str) -> List[Compliance]:
        return self.db.query(Compliance).filter(Compliance.status == status).all()
