from datetime import datetime

from pydantic import BaseModel


class DocumentsCreate(BaseModel):
    name: str
    description: str | None = None


class DocumentsUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DocumentsResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
