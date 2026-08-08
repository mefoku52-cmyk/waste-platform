from typing import List, Optional
from .models import DocumentsModel

class DocumentsService:
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
        item = {"id": new_id, **data}
        self._items.append(item)
        return item
    
    def update(self, id: int, data: dict) -> Optional[dict]:
        for i, item in enumerate(self._items):
            if item.get("id") == id:
                updated = {**item, **data}
                self._items[i] = updated
                return updated
        return None
    
    def delete(self, id: int) -> bool:
        for i, item in enumerate(self._items):
            if item.get("id") == id:
                del self._items[i]
                return True
        return False
