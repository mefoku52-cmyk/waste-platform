"""listings domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.shared.domain.base import BaseEntity


@dataclass
class ListingsEntity(BaseEntity):
    """Listings entity."""
    id: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
