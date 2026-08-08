import os
import sys

modules = [
    'inquiries',
    'documents', 
    'compliance',
    'notifications',
    'analytics',
    'admin'
]

print("--- Spúšťam generátor modulov ---")

for module in modules:
    module_path = f'app/modules/{module}'
    os.makedirs(module_path, exist_ok=True)
    
    # __init__.py
    with open(f'{module_path}/__init__.py', 'w') as f:
        f.write(f'''"""
{module.title()} modul pre Waste Platform.
"""
from .router import router
''')
    
    # models.py
    with open(f'{module_path}/models.py', 'w') as f:
        f.write(f'''from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class {module.title()}Model(BaseModel):
    id: Optional[int] = None
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
''')
    
    # schemas.py
    with open(f'{module_path}/schemas.py', 'w') as f:
        f.write(f'''from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class {module.title()}Create(BaseModel):
    name: str
    description: Optional[str] = None

class {module.title()}Update(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class {module.title()}Response(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
''')
    
    # service.py
    with open(f'{module_path}/service.py', 'w') as f:
        f.write(f'''from typing import List, Optional
from .models import {module.title()}Model

class {module.title()}Service:
    def __init__(self):
        self._items = []
    
    def get_all(self) -> List[dict]:
        return self._items
    
    def get_by_id(self, id: int) -> Optional[dict]:
        for item in self._items:
            if item.get("id") == id:
                return item
        return None
    
    def create(self, data: dict) -> dict:
        new_id = len(self._items) + 1
        item = {{"id": new_id, **data}}
        self._items.append(item)
        return item
    
    def update(self, id: int, data: dict) -> Optional[dict]:
        for i, item in enumerate(self._items):
            if item.get("id") == id:
                updated = {{**item, **data}}
                self._items[i] = updated
                return updated
        return None
    
    def delete(self, id: int) -> bool:
        for i, item in enumerate(self._items):
            if item.get("id") == id:
                del self._items[i]
                return True
        return False
''')
    
    # router.py
    with open(f'{module_path}/router.py', 'w') as f:
        f.write(f'''from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .schemas import {module.title()}Create, {module.title()}Update, {module.title()}Response
from .service import {module.title()}Service

router = APIRouter(prefix="/{module}", tags=["{module.title()}"])

@router.get("/", response_model=List[{module.title()}Response])
async def get_all(
    service: {module.title()}Service = Depends()
):
    """Získa všetky položky"""
    return service.get_all()

@router.get("/{{id}}", response_model={module.title()}Response)
async def get_by_id(
    id: int,
    service: {module.title()}Service = Depends()
):
    """Získa položku podľa ID"""
    item = service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.post("/", response_model={module.title()}Response, status_code=status.HTTP_201_CREATED)
async def create(
    data: {module.title()}Create,
    service: {module.title()}Service = Depends()
):
    """Vytvorí novú položku"""
    return service.create(data.dict())

@router.put("/{{id}}", response_model={module.title()}Response)
async def update(
    id: int,
    data: {module.title()}Update,
    service: {module.title()}Service = Depends()
):
    """Aktualizuje položku"""
    item = service.update(id, data.dict(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return item

@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    service: {module.title()}Service = Depends()
):
    """Vymaže položku"""
    if not service.delete(id):
        raise HTTPException(status_code=404, detail="Položka neexistuje")
    return None
''')
    
    print(f"✅ Vytvorený modul: {module}")

print("✅ Všetky moduly vytvorené!")
print("")
print("Teraz spusti: python3 -c \"from app.main import app; print('OK')\"")
