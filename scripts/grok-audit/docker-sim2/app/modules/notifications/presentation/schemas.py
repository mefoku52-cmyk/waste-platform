"""notifications API schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationsResponse(BaseModel):
    """Notifications response."""
    id: str
    created_at: datetime
    updated_at: datetime


class NotificationsCreateRequest(BaseModel):
    """Create notifications request."""
    pass


class NotificationsUpdateRequest(BaseModel):
    """Update notifications request."""
    pass
