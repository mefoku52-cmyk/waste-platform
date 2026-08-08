from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .schemas import NotificationsCreate, NotificationsUpdate, NotificationsResponse
from .service import NotificationsService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=List[NotificationsResponse])
async def get_all(
    service: NotificationsService = Depends()
):
    """Získa všetky položky"""
    return service.get_all()

@router.get("/{id}", response_model=NotificationsResponse)
async def get_by_id(
    id: int,
    service: NotificationsService = Depends()
):
    """Získa položku podľa ID"""
    item = service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.post("/", response_model=NotificationsResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: NotificationsCreate,
    service: NotificationsService = Depends()
):
    """Vytvorí novú položku"""
    return service.create(data.dict())

@router.put("/{id}", response_model=NotificationsResponse)
async def update(
    id: int,
    data: NotificationsUpdate,
    service: NotificationsService = Depends()
):
    """Aktualizuje položku"""
    item = service.update(id, data.dict(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    service: NotificationsService = Depends()
):
    """Vymaže položku"""
    if not service.delete(id):
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return None
