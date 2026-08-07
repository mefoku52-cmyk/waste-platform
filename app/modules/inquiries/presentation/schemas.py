"""inquiries API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InquiriesResponse(BaseModel):
    """Inquiries response."""
    id: str
    created_at: datetime
    updated_at: datetime


class InquiriesCreateRequest(BaseModel):
    """Create inquiries request."""
    pass


class InquiriesUpdateRequest(BaseModel):
    """Update inquiries request."""
    pass
