"""Partner OAuth 2.0 application and token models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class OAuthScope(str, Enum):
    LISTINGS_READ = "listings:read"
    LISTINGS_WRITE = "listings:write"
    INQUIRIES_READ = "inquiries:read"
    INQUIRIES_WRITE = "inquiries:write"
    COMPANIES_READ = "companies:read"
    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_WRITE = "documents:write"
    ANALYTICS_READ = "analytics:read"
    WEBHOOKS_MANAGE = "webhooks:manage"


class PartnerApplication(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    client_id: str
    client_secret_hash: str
    scopes: list[OAuthScope]
    is_active: bool = True
    created_at: datetime


class PartnerToken(BaseModel):
    id: UUID
    application_id: UUID
    access_token_hash: str
    scopes: list[OAuthScope]
    expires_at: datetime
    revoked: bool = False