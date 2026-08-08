from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt
from jwt.exceptions import InvalidTokenError
import os

# SECRET KEY - používame rovnaký pre všetky tokeny
SECRET_KEY = os.getenv("SECRET_KEY", "my-super-secret-key-change-me-in-production-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

# Simulovaná databáza používateľov (pre prípad, že DB nie je dostupná)
fake_users_db = {
    "admin@example.com": {
        "id": 1,
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": "admin",
        "permissions": ["read_all", "write_all", "delete_all", "manage_users"],
        "is_active": True
    },
    "manager@example.com": {
        "id": 2,
        "email": "manager@example.com",
        "password": "manager123",
        "full_name": "Manager User",
        "role": "manager",
        "permissions": ["read_all", "write_own", "manage_team"],
        "is_active": True
    },
    "user@example.com": {
        "id": 3,
        "email": "user@example.com",
        "password": "user123",
        "full_name": "Regular User",
        "role": "user",
        "permissions": ["read_own", "write_own"],
        "is_active": True
    }
}

def create_access_token(data: Dict[str, Any]) -> str:
    """Vytvorí JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Vytvorí JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Overí JWT token a vráti payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Získa aktuálneho používateľa z tokenu"""
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Najprv skús databázu, potom fake DB
    try:
        from app.shared.database.db import SessionLocal
        from app.shared.models.base import User
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()
        if user:
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "permissions": user.permissions.split(",") if user.permissions else [],
                "is_active": user.is_active
            }
    except:
        pass
    
    # Fallback na fake DB
    user = fake_users_db.get(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Získa aktuálneho používateľa, alebo None ak nie je prihlásený"""
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None

def require_role(required_roles: List[str]):
    """Dekorátor pre kontrolu rolí"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}. Current role: {user_role}"
            )
        return current_user
    return role_checker

def require_permission(required_permission: str):
    """Dekorátor pre kontrolu permissions"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {required_permission}"
            )
        return current_user
    return permission_checker

# Schémy pre Pydantic
from pydantic import BaseModel

class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresIn: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refreshToken: str

class LogoutRequest(BaseModel):
    refreshToken: str
