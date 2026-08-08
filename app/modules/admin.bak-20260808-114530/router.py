from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .schemas import AdminCreate, AdminUpdate, AdminResponse
from .service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/", response_model=List[AdminResponse])
async def get_all(
    service: AdminService = Depends()
):
    """Získa všetky položky"""
    return service.get_all()

@router.get("/{id}", response_model=AdminResponse)
async def get_by_id(
    id: int,
    service: AdminService = Depends()
):
    """Získa položku podľa ID"""
    item = service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: AdminCreate,
    service: AdminService = Depends()
):
    """Vytvorí novú položku"""
    return service.create(data.dict())

@router.put("/{id}", response_model=AdminResponse)
async def update(
    id: int,
    data: AdminUpdate,
    service: AdminService = Depends()
):
    """Aktualizuje položku"""
    item = service.update(id, data.dict(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    service: AdminService = Depends()
):
    """Vymaže položku"""
    if not service.delete(id):
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return None
