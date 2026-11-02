"""Webhook administration router (company-scoped)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import require_company_admin

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreateRequest(BaseModel):
    url: HttpUrl
    events: list[str]
    secret: str | None = None


class WebhookResponse(BaseModel):
    id: UUID
    url: str
    events: list[str]
    is_active: bool


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    payload: WebhookCreateRequest,
    current_user=Depends(require_current_user),
):
    # Placeholder: in full impl resolve company from membership and persist
    raise HTTPException(status_code=501, detail="Webhook creation not yet fully wired")


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(current_user=Depends(require_current_user)):
    return []