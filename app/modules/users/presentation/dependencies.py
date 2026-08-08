from fastapi import Depends
from sqlalchemy.orm import Session
from app.shared.database.db import get_db
from app.modules.users.domain.service import UserService

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)
