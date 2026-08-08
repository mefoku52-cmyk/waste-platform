from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.shared.security import get_current_user, require_permission
from app.modules.listings.presentation.dependencies import get_listing_service
from app.modules.listings.domain.service import ListingService

router = APIRouter(prefix="/listings", tags=["listings"])

@router.get("/")
async def get_all(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ListingService = Depends(get_listing_service)
):
    return service.get_all(
        user_id=current_user.get("id"),
        role=current_user.get("role", "user")
    )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_permission("write_own")),
    service: ListingService = Depends(get_listing_service)
):
    return service.create(data, current_user.get("id"))

@router.get("/{id}")
async def get_by_id(
    id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ListingService = Depends(get_listing_service)
):
    result = service.get_by_id(id, current_user.get("id"), current_user.get("role", "user"))
    if not result:
        raise HTTPException(status_code=404, detail="Listing not found or access denied")
    return result

@router.put("/{id}")
async def update(
    id: int,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_permission("write_own")),
    service: ListingService = Depends(get_listing_service)
):
    result = service.update(id, data, current_user.get("id"), current_user.get("role", "user"))
    if not result:
        raise HTTPException(status_code=404, detail="Listing not found or access denied")
    return result

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    current_user: Dict[str, Any] = Depends(require_permission("write_own")),
    service: ListingService = Depends(get_listing_service)
):
    if not service.delete(id, current_user.get("id"), current_user.get("role", "user")):
        raise HTTPException(status_code=404, detail="Listing not found or access denied")
    return None
