from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .schemas import AnalyticsCreate, AnalyticsUpdate, AnalyticsResponse
from .service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/", response_model=List[AnalyticsResponse])
async def get_all(
    service: AnalyticsService = Depends()
):
    """Získa všetky položky"""
    return service.get_all()

@router.get("/{id}", response_model=AnalyticsResponse)
async def get_by_id(
    id: int,
    service: AnalyticsService = Depends()
):
    """Získa položku podľa ID"""
    item = service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.post("/", response_model=AnalyticsResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: AnalyticsCreate,
    service: AnalyticsService = Depends()
):
    """Vytvorí novú položku"""
    return service.create(data.dict())

@router.put("/{id}", response_model=AnalyticsResponse)
async def update(
    id: int,
    data: AnalyticsUpdate,
    service: AnalyticsService = Depends()
):
    """Aktualizuje položku"""
    item = service.update(id, data.dict(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    service: AnalyticsService = Depends()
):
    """Vymaže položku"""
    if not service.delete(id):
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return None
