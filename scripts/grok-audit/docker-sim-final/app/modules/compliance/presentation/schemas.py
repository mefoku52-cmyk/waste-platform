"""compliance API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ComplianceResponse(BaseModel):
    """Compliance response."""
    id: str
    created_at: datetime
    updated_at: datetime


class ComplianceCreateRequest(BaseModel):
    """Create compliance request."""
    pass


class ComplianceUpdateRequest(BaseModel):
    """Update compliance request."""
    pass
