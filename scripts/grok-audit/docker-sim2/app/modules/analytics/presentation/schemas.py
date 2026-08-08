"""analytics API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AnalyticsResponse(BaseModel):
    """Analytics response."""
    id: str
    created_at: datetime
    updated_at: datetime


class AnalyticsCreateRequest(BaseModel):
    """Create analytics request."""
    pass


class AnalyticsUpdateRequest(BaseModel):
    """Update analytics request."""
    pass
