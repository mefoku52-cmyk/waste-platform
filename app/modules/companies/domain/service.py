import re
from app.shared.models.base import Company

def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

class CompanyService:
    def __init__(self, repository):
        self.repository = repository

    async def create(self, data, owner_id: int):
        raw = data.model_dump() if hasattr(data, "model_dump") else data.dict()
        company_data = {_camel_to_snake(k): v for k, v in raw.items()}
        company_data["owner_id"] = owner_id

        valid_columns = {c.name for c in Company.__table__.columns}
        filtered = {k: v for k, v in company_data.items() if k in valid_columns}

        return await self.repository.create(filtered)

    async def get_all(self, owner_id: int, role: str):
        items = await self.repository.get_all()
        if role == "admin":
            return items
        return [i for i in items if getattr(i, 'owner_id', None) == owner_id]

    async def get_by_id(self, id, owner_id: int, role: str):
        item = await self.repository.get_by_id(id)
        if item is None:
            return None
        if role == "admin" or getattr(item, 'owner_id', None) == owner_id:
            return item
        return None

    async def update(self, id, data, owner_id: int, role: str):
        raw = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
        company_data = {_camel_to_snake(k): v for k, v in raw.items()}

        valid_columns = {c.name for c in Company.__table__.columns}
        filtered = {k: v for k, v in company_data.items() if k in valid_columns}

        item = await self.repository.get_by_id(id)
        if item is None:
            return None
        if role != "admin" and getattr(item, 'owner_id', None) != owner_id:
            return None
        
        return await self.repository.update(id, filtered)

    async def delete(self, id, owner_id: int, role: str):
        item = await self.repository.get_by_id(id)
        if item is None:
            return False
        if role != "admin" and getattr(item, 'owner_id', None) != owner_id:
            return False
        return await self.repository.delete(id)
