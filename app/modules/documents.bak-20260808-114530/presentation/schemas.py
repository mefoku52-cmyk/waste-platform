"""documents API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentsResponse(BaseModel):
    """Documents response."""
    id: str
    created_at: datetime
    updated_at: datetime


class DocumentsCreateRequest(BaseModel):
    """Create documents request."""
    pass


class DocumentsUpdateRequest(BaseModel):
    """Update documents request."""
    pass
