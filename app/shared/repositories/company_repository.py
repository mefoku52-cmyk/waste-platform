from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models.base import Company
from app.shared.repositories.base_repository import BaseRepository

class CompanyRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Company, db)
    
    def get_by_owner_id(self, owner_id: int) -> List[Company]:
        return self.db.query(Company).filter(Company.owner_id == owner_id).all()
    
    def get_by_status(self, status: str) -> List[Company]:
        return self.db.query(Company).filter(Company.status == status).all()
