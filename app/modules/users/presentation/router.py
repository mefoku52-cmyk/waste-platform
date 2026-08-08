from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.shared.security import get_current_user, require_role, require_permission
from app.modules.users.presentation.dependencies import get_user_service
from app.modules.users.domain.service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def get_all(
    current_user: Dict[str, Any] = Depends(require_role(["admin", "manager"])),
    service: UserService = Depends(get_user_service)
):
    """Získa všetkých používateľov (len admin a manager)"""
    return service.get_all(role=current_user.get("role", "user"))

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_permission("manage_users")),
    service: UserService = Depends(get_user_service)
):
    """Vytvorí nového používateľa (vyžaduje manage_users)"""
    return service.create(data)

@router.get("/{user_id}")
async def get_by_id(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Získa používateľa podľa ID"""
    result = service.get_by_id(user_id, current_user.get("id"), current_user.get("role", "user"))
    if not result:
        raise HTTPException(status_code=404, detail="User not found or access denied")
    return result

@router.put("/{user_id}")
async def update(
    user_id: int,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_permission("write_own")),
    service: UserService = Depends(get_user_service)
):
    """Aktualizuje používateľa"""
    result = service.update(user_id, data, current_user.get("id"), current_user.get("role", "user"))
    if not result:
        raise HTTPException(status_code=404, detail="User not found or access denied")
    return result

@router.put("/{user_id}/status")
async def update_status(
    user_id: int,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_permission("manage_users")),
    service: UserService = Depends(get_user_service)
):
    """Aktualizuje status používateľa (vyžaduje manage_users)"""
    result = service.update(user_id, {"is_active": data.get("is_active")}, None, "admin")
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_permission("manage_users")),
    service: UserService = Depends(get_user_service)
):
    """Vymaže používateľa (vyžaduje manage_users)"""
    if not service.delete(user_id, current_user.get("id"), current_user.get("role", "user")):
        raise HTTPException(status_code=404, detail="User not found or access denied")
    return None
