from fastapi import Depends
from sqlalchemy.orm import Session
from app.shared.database.db import get_db
from app.modules.auth.domain.service import AuthService

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency injection pre AuthService"""
    return AuthService(db)
