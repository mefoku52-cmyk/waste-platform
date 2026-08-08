from fastapi import Depends
from sqlalchemy.orm import Session
from app.shared.database.db import get_db
from app.modules.listings.domain.service import ListingService

def get_listing_service(db: Session = Depends(get_db)) -> ListingService:
    return ListingService(db)
