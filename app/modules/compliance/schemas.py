from datetime import datetime

from pydantic import BaseModel


class ComplianceCreate(BaseModel):
    name: str
    description: str | None = None


class ComplianceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ComplianceResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
