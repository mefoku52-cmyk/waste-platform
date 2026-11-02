"""Webhook domain models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class WebhookEventType(str, Enum):
    LISTING_CREATED = "listing.created"
    LISTING_UPDATED = "listing.updated"
    LISTING_PUBLISHED = "listing.published"
    LISTING_DELETED = "listing.deleted"
    INQUIRY_CREATED = "inquiry.created"
    INQUIRY_ANSWERED = "inquiry.answered"
    INQUIRY_CLOSED = "inquiry.closed"
    CONTACT_REVEALED = "contact.revealed"
    COMPANY_UPDATED = "company.updated"
    DOCUMENT_UPLOADED = "document.uploaded"
    PAYMENT_APPLIED = "payment.applied"


class WebhookEndpoint(BaseModel):
    id: UUID
    company_id: UUID
    url: HttpUrl
    secret: str
    events: list[WebhookEventType]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class WebhookDelivery(BaseModel):
    id: UUID
    endpoint_id: UUID
    event_type: WebhookEventType
    payload: dict[str, Any]
    status: str  # pending, delivered, failed, dead_letter
    attempts: int = 0
    next_retry_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime