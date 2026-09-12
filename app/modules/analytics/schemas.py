from datetime import datetime

from pydantic import BaseModel


class AnalyticsCreate(BaseModel):
    name: str
    description: str | None = None


class AnalyticsUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class AnalyticsResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
