from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models.base import Listing
from app.shared.repositories.base_repository import BaseRepository

class ListingRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Listing, db)
    
    def get_by_user_id(self, user_id: int) -> List[Listing]:
        return self.db.query(Listing).filter(Listing.user_id == user_id).all()
    
    def get_by_category(self, category: str) -> List[Listing]:
        return self.db.query(Listing).filter(Listing.category == category).all()
    
    def get_by_status(self, status: str) -> List[Listing]:
        return self.db.query(Listing).filter(Listing.status == status).all()
