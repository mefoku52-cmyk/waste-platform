from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.shared.repositories.document_repository import DocumentRepository
from app.shared.models.base import Document

class DocumentService:
    """Servisná vrstva pre documents"""
    
    def __init__(self, db: Session):
        self.repository = DocumentRepository(db)
        self.db = db
    
    def get_all(self, user_id: Optional[int] = None, role: str = "user") -> List[Dict[str, Any]]:
        if role == "admin":
            documents = self.repository.get_all()
        elif user_id:
            documents = self.repository.get_by_user_id(user_id)
        else:
            documents = []
        return [self._to_dict(doc) for doc in documents]
    
    def get_by_id(self, id: int, user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        doc = self.repository.get_by_id(id)
        if not doc:
            return None
        if role != "admin" and doc.user_id != user_id:
            return None
        return self._to_dict(doc)
    
    def create(self, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        data["user_id"] = user_id
        doc = self.repository.create(data)
        return self._to_dict(doc)
    
    def update(self, id: int, data: Dict[str, Any], user_id: Optional[int] = None, role: str = "user") -> Optional[Dict[str, Any]]:
        doc = self.repository.get_by_id(id)
        if not doc:
            return None
        if role != "admin" and doc.user_id != user_id:
            return None
        updated = self.repository.update(id, data)
        return self._to_dict(updated) if updated else None
    
    def delete(self, id: int, user_id: Optional[int] = None, role: str = "user") -> bool:
        doc = self.repository.get_by_id(id)
        if not doc:
            return False
        if role != "admin" and doc.user_id != user_id:
            return False
        return self.repository.delete(id)
    
    def _to_dict(self, doc: Document) -> Dict[str, Any]:
        return {
            "id": doc.id,
            "user_id": doc.user_id,
            "name": doc.name,
            "description": doc.description,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
        }
