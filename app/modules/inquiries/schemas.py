from datetime import datetime

from pydantic import BaseModel


class InquiriesCreate(BaseModel):
    name: str
    description: str | None = None


class InquiriesUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class InquiriesResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
