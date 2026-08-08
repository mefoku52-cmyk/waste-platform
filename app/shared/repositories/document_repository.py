from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models.base import Document
from app.shared.repositories.base_repository import BaseRepository

class DocumentRepository(BaseRepository):
    """Repository pre Document model"""
    
    def __init__(self, db: Session):
        super().__init__(Document, db)
    
    def get_by_user_id(self, user_id: int) -> List[Document]:
        return self.db.query(Document).filter(Document.user_id == user_id).all()
    
    def get_by_status(self, status: str) -> List[Document]:
        return self.db.query(Document).filter(Document.status == status).all()
