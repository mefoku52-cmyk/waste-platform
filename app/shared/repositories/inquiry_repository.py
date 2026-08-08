from sqlalchemy.orm import Session
from typing import List
from app.shared.models.base import Inquiry
from app.shared.repositories.base_repository import BaseRepository

class InquiryRepository(BaseRepository):
    """Repository pre Inquiry model"""
    
    def __init__(self, db: Session):
        super().__init__(Inquiry, db)
    
    def get_by_user_id(self, user_id: int) -> List[Inquiry]:
        return self.db.query(Inquiry).filter(Inquiry.user_id == user_id).all()
    
    def get_by_status(self, status: str) -> List[Inquiry]:
        return self.db.query(Inquiry).filter(Inquiry.status == status).all()
