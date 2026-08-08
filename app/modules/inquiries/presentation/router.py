from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.shared.security import get_current_user

router = APIRouter(prefix="/inquiries", tags=["inquiries"])

# In-memory storage
_items = []
_counter = 0

@router.get("/")
async def get_all(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Získa všetky položky (chránené)"""
    return _items

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Vytvorí novú položku (chránené)"""
    global _counter
    _counter += 1
    item = {"id": _counter, **data}
    _items.append(item)
    return item

@router.get("/{id}")
async def get_by_id(id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Získa položku podľa ID (chránené)"""
    for item in _items:
        if item.get("id") == id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@router.put("/{id}")
async def update(id: int, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Aktualizuje položku (chránené)"""
    for i, item in enumerate(_items):
        if item.get("id") == id:
            updated = {**item, **data}
            _items[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Item not found")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Vymaže položku (chránené)"""
    for i, item in enumerate(_items):
        if item.get("id") == id:
            del _items[i]
            return
    raise HTTPException(status_code=404, detail="Item not found")
