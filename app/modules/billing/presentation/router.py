from __future__ import annotations

import base64
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.config import settings
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import current_user_id

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
    return (
        all(cfg[k] for k in ("client_id", "client_secret", "goid", "return_url", "notify_url"))
        and cfg["goid"].isdigit()
    )


def _goid_int(cfg: dict[str, str]) -> int:
    try:
        return int(cfg["goid"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=503, detail="gopay_misconfigured")


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
        "target": {"type": "ACCOUNT", "goid": _goid_int(cfg)},
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


@router.api_route("/notify", methods=["GET", "POST"])
async def billing_notify(request: Request, session=Depends(get_db_session)):
    cfg = _cfg()
    if not _ready(cfg):
        raise HTTPException(status_code=503, detail="gopay_not_configured")
    payment_id = request.query_params.get("id") or ""
    if not payment_id and request.method == "POST":
        form = await request.form()
        payment_id = str(form.get("id") or "")
    if not payment_id:
        raise HTTPException(status_code=400, detail="payment_id_missing")
    data = await _payment(cfg, payment_id)
    state = str(data.get("state") or "")
    company_id = _param(data, "company_id")
    tier = _param(data, "tier") or "pro"
    updated = 0
    if state == "PAID" and company_id and tier == "pro":
        result = await session.execute(
            text(
                """
                UPDATE companies
                SET subscription_tier = 'pro'
                WHERE id::text = :company_id
                """
            ),
            {"company_id": company_id},
        )
        updated = int(result.rowcount or 0)
        await session.commit()
    return {"ok": True, "state": state, "updated": updated}


async def _payment(cfg: dict[str, str], payment_id: str) -> dict:
    token = await _token(cfg)
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{cfg['api']}/api/payments/payment/{payment_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="gopay_status_failed")
    return resp.json()


def _param(data: dict, name: str) -> str:
    for row in data.get("additional_params") or []:
        if str(row.get("name")) == name:
            return str(row.get("value") or "")
    return ""

# ============================================================
# Stripe integration
# ============================================================

import stripe


class _StripeCheckoutIn(BaseModel):
    kind: str = Field(default="promote", max_length=32)
    listing_id: str | None = None
    days: int = Field(default=7, ge=1, le=365)
    tier: str = Field(default="top", max_length=16)
    success_url: str = Field(min_length=1, max_length=500)
    cancel_url: str = Field(min_length=1, max_length=500)


def _stripe_prices() -> dict[tuple[str, int], int]:
    return {
        ("top", 7): 500,
        ("top", 30): 1000,
        ("gold", 30): 3000,
    }


@router.post("/stripe/checkout")
async def stripe_checkout(
    body: _StripeCheckoutIn,
    current_user=Depends(require_current_user),
):
    secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not secret:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    stripe.api_key = secret

    amount = _stripe_prices().get((body.tier, body.days))
    if amount is None:
        raise HTTPException(status_code=422, detail="Unknown tier/days combo")
    if body.kind == "promote" and not body.listing_id:
        raise HTTPException(status_code=422, detail="listing_id required for promote")

    try:
        user_id = str(current_user_id(current_user) or "")
    except Exception:
        user_id = ""

    try:
        cs = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "unit_amount": amount,
                    "product_data": {
                        "name": f"CMEP {'TOP' if body.tier == 'top' else 'GOLD'} {body.days} dni",
                    },
                },
                "quantity": 1,
            }],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={
                "kind": body.kind,
                "listing_id": body.listing_id or "",
                "days": str(body.days),
                "tier": body.tier,
                "user_id": user_id,
            },
        )
        return {"url": cs.url, "id": cs.id}
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=400, detail=f"Stripe error: {getattr(exc, 'user_message', None) or str(exc)}")


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, session=Depends(get_db_session)):
    secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
    if not secret or not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")

    stripe.api_key = secret
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        sess = event["data"]["object"]
        md = sess.get("metadata", {}) or {}
        if md.get("kind") == "promote" and md.get("listing_id"):
            try:
                from app.modules.listings.presentation.dependencies import get_listings_service
                svc = get_listings_service(session=session)
                await svc.promote(
                    md["listing_id"],
                    days=int(md.get("days", "7")),
                    tier=md.get("tier", "top"),
                )
            except Exception:
                pass

    return {"received": True}
