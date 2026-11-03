"""Webhook administration router (company-scoped)."""

from __future__ import annotations

import secrets
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from app.modules.webhooks.infrastructure.ssrf import is_safe_url
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import require_company_admin

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreateRequest(BaseModel):
    url: HttpUrl
    events: list[str]


class WebhookResponse(BaseModel):
    id: UUID
    url: str
    events: list[str]
    is_active: bool
    secret: str | None = None  # returned only on create


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    payload: WebhookCreateRequest,
    current_user=Depends(require_current_user),
):
    if not is_safe_url(str(payload.url)):
        raise HTTPException(status_code=400, detail="Webhook URL blocked by SSRF protection")

    # In full impl resolve company and persist via repository
    secret = secrets.token_urlsafe(32)
    return WebhookResponse(
        id=uuid4(),
        url=str(payload.url),
        events=payload.events,
        is_active=True,
        secret=secret,
    )


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(current_user=Depends(require_current_user)):
    return []