from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .schemas import InquiriesCreate, InquiriesUpdate, InquiriesResponse
from .service import InquiriesService

router = APIRouter(prefix="/inquiries", tags=["Inquiries"])

@router.get("/", response_model=List[InquiriesResponse])
async def get_all(
    service: InquiriesService = Depends()
):
    """Získa všetky položky"""
    return service.get_all()

@router.get("/{id}", response_model=InquiriesResponse)
async def get_by_id(
    id: int,
    service: InquiriesService = Depends()
):
    """Získa položku podľa ID"""
    item = service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.post("/", response_model=InquiriesResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: InquiriesCreate,
    service: InquiriesService = Depends()
):
    """Vytvorí novú položku"""
    return service.create(data.dict())

@router.put("/{id}", response_model=InquiriesResponse)
async def update(
    id: int,
    data: InquiriesUpdate,
    service: InquiriesService = Depends()
):
    """Aktualizuje položku"""
    item = service.update(id, data.dict(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    service: InquiriesService = Depends()
):
    """Vymaže položku"""
    if not service.delete(id):
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return None
