"""
Legacy compatibility service for documents module.
"""

import warnings
from typing import List, Optional


class DocumentsService:
    def __init__(self):
        warnings.warn(
            "DocumentsService is a legacy compatibility shim; migrate to presentation layer.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._items: List[dict] = []

    def get_all(self) -> List[dict]:
        return self._items

    def get_by_id(self, id: int) -> Optional[dict]:
        return next((i for i in self._items if i.get("id") == id), None)

    def create(self, data: dict) -> dict:
        item = {"id": len(self._items) + 1, **data}
        self._items.append(item)
        return item

    def update(self, id: int, data: dict) -> Optional[dict]:
        for i, item in enumerate(self._items):
            if item.get("id") == id:
                self._items[i] = {**item, **data}
                return self._items[i]
        return None

    def delete(self, id: int) -> bool:
        for i, item in enumerate(self._items):
            if item.get("id") == id:
                del self._items[i]
                return True
        return False
