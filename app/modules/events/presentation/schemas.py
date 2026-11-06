from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    eventType: str = Field(min_length=3, max_length=64)
    companyId: str | None = None
    listingId: str | None = None
    # Frontend posiela payload ako objekt (napr. {"reason": ...}) aj ako string.
    # Serializacia a limit 2000 znakov sa riesi v routeri pred ulozenim do Text stlpca.
    payload: Any = None


class EventOut(BaseModel):
    id: str
    eventType: str
