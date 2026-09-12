from datetime import datetime

from pydantic import BaseModel


class AdminCreate(BaseModel):
    name: str
    description: str | None = None


class AdminUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class AdminResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
