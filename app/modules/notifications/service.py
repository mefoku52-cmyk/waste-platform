"""
Legacy compatibility service for notifications module.
"""

import warnings


class NotificationsService:
    def __init__(self):
        warnings.warn(
            "NotificationsService is a legacy compatibility shim; migrate to presentation layer.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._items: list[dict] = []

    def get_all(self) -> list[dict]:
        return self._items

    def get_by_id(self, id: int) -> dict | None:
        return next((i for i in self._items if i.get("id") == id), None)

    def create(self, data: dict) -> dict:
        item = {"id": len(self._items) + 1, **data}
        self._items.append(item)
        return item

    def update(self, id: int, data: dict) -> dict | None:
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
