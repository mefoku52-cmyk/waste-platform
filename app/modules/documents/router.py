from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .schemas import DocumentsCreate, DocumentsUpdate, DocumentsResponse
from .service import DocumentsService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/", response_model=List[DocumentsResponse])
async def get_all(
    service: DocumentsService = Depends()
):
    """Získa všetky položky"""
    return service.get_all()

@router.get("/{id}", response_model=DocumentsResponse)
async def get_by_id(
    id: int,
    service: DocumentsService = Depends()
):
    """Získa položku podľa ID"""
    item = service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.post("/", response_model=DocumentsResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: DocumentsCreate,
    service: DocumentsService = Depends()
):
    """Vytvorí novú položku"""
    return service.create(data.dict())

@router.put("/{id}", response_model=DocumentsResponse)
async def update(
    id: int,
    data: DocumentsUpdate,
    service: DocumentsService = Depends()
):
    """Aktualizuje položku"""
    item = service.update(id, data.dict(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    service: DocumentsService = Depends()
):
    """Vymaže položku"""
    if not service.delete(id):
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return None
