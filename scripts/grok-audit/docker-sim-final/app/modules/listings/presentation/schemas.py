"""listings API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ListingsResponse(BaseModel):
    """Listings response."""
    id: str
    created_at: datetime
    updated_at: datetime


class ListingsCreateRequest(BaseModel):
    """Create listings request."""
    pass


class ListingsUpdateRequest(BaseModel):
    """Update listings request."""
    pass
