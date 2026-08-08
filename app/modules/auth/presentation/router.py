from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.shared.security import (
    get_current_user,
    verify_token,
    create_access_token,
    create_refresh_token,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    TokenResponse,
    fake_users_db
)
import os

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory storage pre refresh tokeny
refresh_tokens = {}

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Prihlásenie používateľa"""
    
    # Najprv skús databázu
    try:
        from app.shared.database.db import SessionLocal
        from app.shared.models.base import User
        db = SessionLocal()
        user = db.query(User).filter(User.email == data.email).first()
        db.close()
        
        if user and user.password == data.password and user.is_active:
            access_token = create_access_token({"sub": user.email, "role": user.role})
            refresh_token = create_refresh_token({"sub": user.email, "role": user.role})
            refresh_tokens[refresh_token] = user.email
            return TokenResponse(
                accessToken=access_token,
                refreshToken=refresh_token,
                tokenType="bearer",
                expiresIn=1800
            )
    except:
        pass
    
    # Fallback na fake DB
    user = fake_users_db.get(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token = create_access_token({"sub": user["email"], "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user["email"], "role": user["role"]})
    refresh_tokens[refresh_token] = user["email"]
    
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer",
        expiresIn=1800
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """Obnoví access token"""
    refresh_token = data.refreshToken
    
    if refresh_token not in refresh_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    payload = verify_token(refresh_token, "refresh")
    email = payload.get("sub")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Získaj používateľa
    user = None
    try:
        from app.shared.database.db import SessionLocal
        from app.shared.models.base import User
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()
    except:
        user = fake_users_db.get(email)
    
    if not user or not user.get("is_active") if isinstance(user, dict) else not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    role = user.get("role") if isinstance(user, dict) else user.role
    
    new_access_token = create_access_token({"sub": email, "role": role})
    new_refresh_token = create_refresh_token({"sub": email, "role": role})
    
    del refresh_tokens[refresh_token]
    refresh_tokens[new_refresh_token] = email
    
    return TokenResponse(
        accessToken=new_access_token,
        refreshToken=new_refresh_token,
        tokenType="bearer",
        expiresIn=1800
    )

@router.post("/logout")
async def logout(
    data: LogoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Odhlásenie používateľa"""
    refresh_token = data.refreshToken
    if refresh_token in refresh_tokens:
        del refresh_tokens[refresh_token]
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Získa informácie o aktuálnom používateľovi"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "permissions": current_user.get("permissions", []),
        "is_active": current_user.get("is_active", True)
    }
