from pydantic import BaseModel, Field


class EventIn(BaseModel):
    eventType: str = Field(min_length=3, max_length=64)
    companyId: str | None = None
    listingId: str | None = None
    payload: str | None = Field(default=None, max_length=2000)


class EventOut(BaseModel):
    id: str
    eventType: str
