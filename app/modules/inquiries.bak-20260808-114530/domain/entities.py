"""inquiries domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.shared.domain.base import BaseEntity


@dataclass
class InquiriesEntity(BaseEntity):
    """Inquiries entity."""
    id: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
