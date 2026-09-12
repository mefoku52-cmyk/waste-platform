from datetime import datetime

from pydantic import BaseModel


class NotificationsCreate(BaseModel):
    name: str
    description: str | None = None


class NotificationsUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class NotificationsResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
