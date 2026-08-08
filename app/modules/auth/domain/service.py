from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.shared.repositories.user_repository import UserRepository
from app.shared.models.base import User
import jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class AuthService:
    """Servisná vrstva pre autentifikáciu - používa databázu"""
    
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.db = db
    
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Prihlásenie používateľa"""
        user = self.repository.get_by_email(email)
        if not user or user.password != password:  # V produkcii používaj hash!
            return None
        if not user.is_active:
            return None
        
        # Vytvor tokeny
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)
        
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "bearer",
            "expiresIn": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Získa používateľa podľa emailu"""
        user = self.repository.get_by_email(email)
        if not user:
            return None
        return self._user_to_dict(user)
    
    def _create_access_token(self, user: User) -> str:
        """Vytvorí access token"""
        payload = {
            "sub": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "type": "access"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def _create_refresh_token(self, user: User) -> str:
        """Vytvorí refresh token"""
        payload = {
            "sub": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "type": "refresh"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Konvertuje User model na dict"""
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "permissions": user.permissions.split(",") if user.permissions else [],
            "is_active": user.is_active
        }
