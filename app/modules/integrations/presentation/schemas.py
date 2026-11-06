from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConnectionCreateRequest(BaseModel):
    integration_type: str = Field(min_length=3, max_length=50)
    credentials: dict[str, Any] = Field(min_length=1)


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    integration_type: str
    status: str
    last_sync_at: datetime | None = None


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str


class SyncResponse(BaseModel):
    success: bool
    message: str
