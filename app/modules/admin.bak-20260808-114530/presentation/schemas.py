"""admin API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdminResponse(BaseModel):
    """Admin response."""
    id: str
    created_at: datetime
    updated_at: datetime


class AdminCreateRequest(BaseModel):
    """Create admin request."""
    pass


class AdminUpdateRequest(BaseModel):
    """Update admin request."""
    pass
