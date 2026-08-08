"""analytics domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.shared.domain.base import BaseEntity


@dataclass
class AnalyticsEntity(BaseEntity):
    """Analytics entity."""

    id: Optional[str] = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
