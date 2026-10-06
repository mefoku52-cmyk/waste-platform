"""Acquisition tracking built on top of the existing analytics event system."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.modules.analytics.domain.entities import AnalyticsEventEntity
from app.modules.analytics.domain.repositories import AnalyticsEventRepository

ALLOWED_EVENTS = frozenset(
    {
        "page_view",
        "landing_view",
        "registration_started",
        "registration_completed",
        "company_created",
        "listing_created",
        "inquiry_created",
        "match_created",
        "chat_started",
        "deal_created",
    }
)

UTM_FIELDS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
)


@dataclass(slots=True)
class AcquisitionEventInput:
    event_type: str
    entity_type: str = "acquisition"
    entity_id: UUID | None = None
    company_id: UUID | None = None

    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None

    anonymous_id: str | None = None
    fbp: str | None = None
    fbc: str | None = None

    landing_page: str | None = None
    referrer: str | None = None


class AcquisitionTrackingService:
    """Records acquisition events using the existing analytics repository."""

    def __init__(self, repository: AnalyticsEventRepository):
        self.repository = repository

    async def record(
        self,
        data: AcquisitionEventInput,
    ) -> AnalyticsEventEntity:
        event_type = data.event_type.strip()

        if event_type not in ALLOWED_EVENTS:
            raise ValueError(f"Unsupported acquisition event: {event_type}")

        metadata: dict[str, Any] = {
            "source": "acquisition",
            "schema_version": 1,
        }

        for field_name in UTM_FIELDS:
            value = getattr(data, field_name)
            if value:
                metadata[field_name] = value.strip()

        optional_fields = {
            "anonymous_id": data.anonymous_id,
            "fbp": data.fbp,
            "fbc": data.fbc,
            "landing_page": data.landing_page,
            "referrer": data.referrer,
        }

        for key, value in optional_fields.items():
            if value:
                metadata[key] = value.strip()

        entity = AnalyticsEventEntity(
            event_type=event_type,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            company_id=data.company_id,
            recorded_at=datetime.now(UTC).replace(tzinfo=None),
            event_metadata=json.dumps(
                metadata,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

        entity.validate()

        return await self.repository.create(entity)
