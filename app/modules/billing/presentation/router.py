from __future__ import annotations

import base64
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.config import settings
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    company_id: str
    tier: str = Field(default="pro")


def _cfg() -> dict[str, str]:
    return {
        "client_id": str(getattr(settings, "GOPAY_CLIENT_ID", "") or "").strip(),
        "client_secret": str(getattr(settings, "GOPAY_CLIENT_SECRET", "") or "").strip(),
        "goid": str(getattr(settings, "GOPAY_GOID", "") or "").strip(),
        "api": str(getattr(settings, "GOPAY_API_URL", "") or "https://gw.sandbox.gopay.com").rstrip(
            "/"
        ),
        "return_url": str(getattr(settings, "GOPAY_RETURN_URL", "") or "").strip(),
        "notify_url": str(getattr(settings, "GOPAY_NOTIFY_URL", "") or "").strip(),
    }


def _ready(cfg: dict[str, str]) -> bool:
    return all(cfg[k] for k in ("client_id", "client_secret", "goid", "return_url", "notify_url"))


async def _token(cfg: dict[str, str]) -> str:
    raw = f"{cfg['client_id']}:{cfg['client_secret']}".encode()
    headers = {
        "Authorization": "Basic " + base64.b64encode(raw).decode(),
        "Accept": "application/json",
    }
    data = urlencode({"grant_type": "client_credentials", "scope": "payment-create"}).encode()
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(cfg["api"] + "/api/oauth2/token", content=data, headers=headers)
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="gopay_token_failed")
    token = str(resp.json().get("access_token") or "")
    if not token:
        raise HTTPException(status_code=502, detail="gopay_token_empty")
    return token


@router.get("/status")
async def billing_status(current_user=Depends(require_current_user)):
    del current_user
    cfg = _cfg()
    amount = int(getattr(settings, "GOPAY_PRO_AMOUNT_CENTS", 0) or 0)
    return {
        "provider": "gopay",
        "configured": _ready(cfg) and amount > 0,
        "tier": "pro",
        "amount_cents": amount,
    }


@router.post("/checkout")
async def billing_checkout(
    payload: CheckoutRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    if payload.tier != "pro":
        raise HTTPException(status_code=400, detail="only_pro")
    cfg = _cfg()
    amount = int(getattr(settings, "GOPAY_PRO_AMOUNT_CENTS", 0) or 0)
    if not _ready(cfg) or amount <= 0:
        raise HTTPException(status_code=503, detail="gopay_not_configured")
    order = uuid.uuid4().hex[:20]
    token = await _token(cfg)
    body = {
        "amount": amount,
        "currency": "EUR",
        "order_number": order,
        "order_description": "CMEP PRO",
        "target": {"type": "ACCOUNT", "goid": int(cfg["goid"])},
        "callback": {"return_url": cfg["return_url"], "notification_url": cfg["notify_url"]},
        "additional_params": [
            {"name": "company_id", "value": payload.company_id},
            {"name": "tier", "value": "pro"},
        ],
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            cfg["api"] + "/api/payments/payment",
            json=body,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="gopay_create_failed")
    data = resp.json()
    await session.execute(
        text(
            """
            INSERT INTO audit_logs (id, action, details, created_at)
            SELECT gen_random_uuid(), 'billing.checkout_created', :details, now()
            WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs')
            """
        ),
        {"details": f"company_id={payload.company_id},order={order},payment={data.get('id')}"},
    )
    await session.commit()
    return {
        "ok": True,
        "order_number": order,
        "gw_url": data.get("gw_url"),
        "payment_id": data.get("id"),
    }
