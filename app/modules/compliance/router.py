from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .schemas import ComplianceCreate, ComplianceUpdate, ComplianceResponse
from .service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["Compliance"])

@router.get("/", response_model=List[ComplianceResponse])
async def get_all(
    service: ComplianceService = Depends()
):
    """Získa všetky položky"""
    return service.get_all()

@router.get("/{id}", response_model=ComplianceResponse)
async def get_by_id(
    id: int,
    service: ComplianceService = Depends()
):
    """Získa položku podľa ID"""
    item = service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.post("/", response_model=ComplianceResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: ComplianceCreate,
    service: ComplianceService = Depends()
):
    """Vytvorí novú položku"""
    return service.create(data.dict())

@router.put("/{id}", response_model=ComplianceResponse)
async def update(
    id: int,
    data: ComplianceUpdate,
    service: ComplianceService = Depends()
):
    """Aktualizuje položku"""
    item = service.update(id, data.dict(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    service: ComplianceService = Depends()
):
    """Vymaže položku"""
    if not service.delete(id):
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return None
