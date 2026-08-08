from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from datetime import timedelta
from typing import Dict, Any

from app.shared.security import (
    fake_users_db,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    TokenResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# In-memory storage pre refresh tokeny (v produkcii daj do Redis/DB)
refresh_tokens = {}

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Prihlásenie používateľa"""
    user = fake_users_db.get(data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # V produkcii používaj hashovanie!
    if user["password"] != data.password:
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
    
    access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    refresh_token = create_refresh_token(data={"sub": user["email"], "role": user["role"]})
    
    # Ulož refresh token
    refresh_tokens[refresh_token] = user["email"]
    
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer",
        expiresIn=30 * 60  # 30 minút
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """Obnoví access token pomocou refresh tokenu"""
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
    
    user = fake_users_db.get(email)
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Vytvor nové tokeny
    new_access_token = create_access_token(data={"sub": email, "role": user["role"]})
    new_refresh_token = create_refresh_token(data={"sub": email, "role": user["role"]})
    
    # Vymeň refresh tokeny
    del refresh_tokens[refresh_token]
    refresh_tokens[new_refresh_token] = email
    
    return TokenResponse(
        accessToken=new_access_token,
        refreshToken=new_refresh_token,
        tokenType="bearer",
        expiresIn=30 * 60
    )

@router.post("/logout")
async def logout(data: LogoutRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Odhlásenie používateľa"""
    refresh_token = data.refreshToken
    
    if refresh_token in refresh_tokens:
        del refresh_tokens[refresh_token]
    
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Získa informácie o aktuálnom používateľovi"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "is_active": current_user["is_active"]
    }
