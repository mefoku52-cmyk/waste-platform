from __future__ import annotations

import base64
import logging
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import urlencode, urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import or_, select, update

from app.core.config import settings
from app.modules.billing.infrastructure.models import BillingPaymentOrderModel
from app.modules.companies.infrastructure.models import CompanyModel
from app.modules.listings.infrastructure.models import ListingsModel
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    require_company_admin,
    require_company_member,
)

router = APIRouter(prefix="/billing", tags=["billing"])


def _current_actor_id(user) -> str:
    actor_id = current_user_id(user)
    if not actor_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return str(actor_id)


def _validate_checkout_urls(success_url: str, cancel_url: str) -> None:
    configured = getattr(settings, "CORS_ORIGINS", []) or []
    if isinstance(configured, str):
        configured = [part.strip() for part in configured.split(",") if part.strip()]
    allowed = {str(origin).rstrip("/") for origin in configured}
    if str(getattr(settings, "app_env", "")).lower() in {"development", "test"}:
        allowed.update({"http://localhost:3000", "http://127.0.0.1:3000"})
    for raw in (success_url, cancel_url):
        parsed = urlsplit(raw)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
        if (
            parsed.scheme not in {"https", "http"}
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or origin not in allowed
            or not parsed.path.startswith("/")
            or raw.startswith("//")
        ):
            raise HTTPException(status_code=422, detail="Checkout return URL is not allowed")


def _new_order(*, provider: str, actor_id: str, company_id: str, kind: str,
               tier: str, amount_cents: int, listing_id: str | None = None,
               duration_days: int | None = None) -> BillingPaymentOrderModel:
    return BillingPaymentOrderModel(
        order_ref=uuid.uuid4().hex,
        provider=provider,
        user_id=actor_id,
        company_id=str(company_id),
        listing_id=listing_id,
        product_kind=kind,
        tier=tier,
        duration_days=duration_days,
        amount_cents=amount_cents,
        currency="EUR",
        status="pending",
    )


def _stripe_int(value: object, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid payment {field}")


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
    # GoPay currently sells only the configured PRO one-time purchase. Other
    # tiers require distinct catalog prices and are intentionally rejected.
    if payload.tier != "pro":
        raise HTTPException(status_code=422, detail="unsupported_tier")
    require_company_admin(current_user, payload.company_id, action="purchase subscription for")
    actor_id = _current_actor_id(current_user)
    company = await session.get(CompanyModel, str(payload.company_id))
    if company is None:
        raise HTTPException(status_code=404, detail="company_not_found")
    cfg = _cfg()
    amount = int(getattr(settings, "GOPAY_PRO_AMOUNT_CENTS", 0) or 0)
    if not _ready(cfg) or amount <= 0:
        raise HTTPException(status_code=503, detail="gopay_not_configured")

        order_ref = uuid.uuid4().hex[:20]
    order = BillingPaymentOrderModel(
        order_ref=order_ref,
        provider="gopay",
        user_id=actor_id,
        company_id=str(company.id),
        product_kind="subscription",
        tier="pro",
        amount_cents=amount,
        currency="EUR",
        status="pending",
    )
    session.add(order)
    await session.commit()

    try:
        token = await _token(cfg)
        body = {
            "amount": amount,
            "currency": "EUR",
            "order_number": order_ref,
            "order_description": "CMEP PRO",
            "target": {"type": "ACCOUNT", "goid": _goid_int(cfg)},
            "callback": {"return_url": cfg["return_url"], "notification_url": cfg["notify_url"]},
            "additional_params": [
                {"name": "order_ref", "value": order_ref},
                {"name": "company_id", "value": str(company.id)},
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
        provider_ref = str(data.get("id") or "")
        if not provider_ref:
            raise HTTPException(status_code=502, detail="gopay_payment_id_missing")
        order.provider_ref = provider_ref
        order.status = "pending"
        await session.commit()
        logger.info("gopay.checkout.created order_ref=%s", order_ref)
        return {"ok": True, "order_number": order_ref, "gw_url": data.get("gw_url"), "payment_id": provider_ref}
    except Exception:
        await session.rollback()
        failed = await session.get(BillingPaymentOrderModel, order.id)
        if failed is not None and failed.status == "pending":
            failed.status = "failed"
            await session.commit()
        raise


@router.get("/notify", operation_id="gopay_notify_get")
@router.post("/notify", operation_id="gopay_notify_post")
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

    # GoPay notification is only a pointer. Entitlements come from the local
    # order written before checkout, never from caller-controlled extra params.
    data = await _payment(cfg, payment_id)
    returned_id = str(data.get("id") or "")
    if returned_id and returned_id != str(payment_id):
        raise HTTPException(status_code=400, detail="payment_id_mismatch")
    provider_ref = returned_id or str(payment_id)
    order_ref = str(data.get("order_number") or _param(data, "order_ref") or "")
    order_lookup = (
        or_(
            BillingPaymentOrderModel.provider_ref == provider_ref,
            BillingPaymentOrderModel.order_ref == order_ref,
        )
        if order_ref
        else BillingPaymentOrderModel.provider_ref == provider_ref
    )
    result = await session.execute(
        select(BillingPaymentOrderModel)
        .where(
            BillingPaymentOrderModel.provider == "gopay",
            order_lookup,
        )
        .with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="payment_order_not_found")
    state = str(data.get("state") or "")
    if order.status == "applied":
        return {"ok": True, "state": state, "updated": 0}
    if state != "PAID":
        return {"ok": True, "state": state, "updated": 0}
    if int(data.get("amount", -1)) != order.amount_cents:
        raise HTTPException(status_code=400, detail="payment_amount_mismatch")
    if str(data.get("currency") or "").upper() != order.currency:
        raise HTTPException(status_code=400, detail="payment_currency_mismatch")
    if order.product_kind != "subscription" or order.tier != "pro":
        raise HTTPException(status_code=400, detail="unsupported_payment_order")

    company = await session.get(CompanyModel, order.company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="company_not_found")
    company.subscription_tier = order.tier
    order.status = "applied"
    order.processed_at = datetime.now(UTC)
    await session.commit()
    return {"ok": True, "state": state, "updated": 1}


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
    kind: Literal["promote"] = "promote"
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


logger = logging.getLogger(__name__)

# Secrets that must never reach the logs, even if embedded in an error message.
_STRIPE_SECRET_PATTERNS = (
    re.compile(r"sk_(?:live|test)_[A-Za-z0-9]+"),
    re.compile(r"pk_(?:live|test)_[A-Za-z0-9]+"),
    re.compile(r"whsec_[A-Za-z0-9]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"),
)

# Errors caused by server-side configuration, not by the caller's request.
_STRIPE_CONFIG_ERRORS = (
    stripe.error.AuthenticationError,
    stripe.error.PermissionError,
)


def _redact(text: object, *, limit: int = 300) -> str:
    """Strip secret-looking tokens and truncate a message for safe logging."""
    out = "" if text is None else str(text)
    for pattern in _STRIPE_SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    if len(out) > limit:
        out = out[:limit] + "...(truncated)"
    return out


def _stripe_error_fields(exc: stripe.error.StripeError) -> dict[str, str]:
    error_obj = getattr(exc, "error", None)
    err_type = getattr(error_obj, "type", None) or getattr(exc, "type", None)
    err_code = getattr(exc, "code", None) or getattr(error_obj, "code", None)
    raw_message = getattr(exc, "user_message", None) or getattr(exc, "message", None) or str(exc)
    return {
        "error_class": type(exc).__name__,
        "error_type": str(err_type or "-"),
        "error_code": str(err_code or "-"),
        "stripe_request_id": str(getattr(exc, "request_id", None) or "-"),
        "message": _redact(raw_message),
    }


def _log_stripe_error(exc: stripe.error.StripeError) -> str:
    """Log a safe subset of a Stripe error. Returns a correlation id.

    Never logs the API key, the full request, headers or payment data.
    """
    correlation_id = uuid.uuid4().hex[:12]
    fields = _stripe_error_fields(exc)
    logger.warning(
        "stripe.checkout failed correlation_id=%s class=%s type=%s code=%s "
        "request_id=%s message=%s",
        correlation_id,
        fields["error_class"],
        fields["error_type"],
        fields["error_code"],
        fields["stripe_request_id"],
        fields["message"],
    )
    return correlation_id


def _stripe_failure(exc: stripe.error.StripeError) -> HTTPException:
    """Map a Stripe error to an appropriate HTTP status + safe client detail."""
    _log_stripe_error(exc)

    if isinstance(exc, _STRIPE_CONFIG_ERRORS):
        # Misconfigured live/test key or insufficient permissions: server-side
        # setup issue. Do not leak the raw provider message to the client.
        return HTTPException(status_code=503, detail="Payment provider is not configured")

    if isinstance(exc, stripe.error.RateLimitError):
        return HTTPException(status_code=429, detail="Payment provider is busy, try again")

    if isinstance(exc, stripe.error.APIConnectionError):
        return HTTPException(status_code=502, detail="Payment provider is unreachable")

    if isinstance(exc, (stripe.error.InvalidRequestError, stripe.error.CardError)):
        message = getattr(exc, "user_message", None) or getattr(exc, "message", None) or str(exc)
        return HTTPException(status_code=400, detail=f"Stripe error: {_redact(message, limit=200)}")

    # Unexpected provider failure.
    return HTTPException(status_code=502, detail="Payment provider error")


@router.post("/stripe/checkout")
async def stripe_checkout(
    body: _StripeCheckoutIn,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not secret:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    stripe.api_key = secret

    amount = _stripe_prices().get((body.tier, body.days))
    if amount is None:
        raise HTTPException(status_code=422, detail="Unknown tier/days combo")
    if not body.listing_id:
        raise HTTPException(status_code=422, detail="listing_id required for promote")
    _validate_checkout_urls(body.success_url, body.cancel_url)
    try:
        listing_uuid = uuid.UUID(body.listing_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid listing_id")
    listing = await session.get(ListingsModel, listing_uuid)
    if listing is None:
        raise HTTPException(status_code=404, detail="listing_not_found")
    require_company_member(current_user, listing.company_id, action="purchase promotion for")
    actor_id = _current_actor_id(current_user)
    order = _new_order(
        provider="stripe",
        actor_id=actor_id,
        company_id=str(listing.company_id),
        kind="promotion",
        tier=body.tier,
        amount_cents=amount,
        listing_id=str(listing.id),
        duration_days=body.days,
    )
    session.add(order)
    await session.commit()
    metadata = {
        "kind": "promote",
        "order_ref": order.order_ref,
        "listing_id": str(listing.id),
        "company_id": str(listing.company_id),
        "days": str(body.days),
        "tier": body.tier,
        "user_id": actor_id,
    }
    try:
        cs = stripe.checkout.Session.create(
            mode="payment",
            allowed_payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": amount,
                        "product_data": {"name": f"CMEP {'TOP' if body.tier == 'top' else 'GOLD'} {body.days} dni"},
                    },
                    "quantity": 1,
                }
            ],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata=metadata,
        )
        order.provider_ref = str(cs.id)
        await session.commit()
        return {"url": cs.url, "id": cs.id}
    except stripe.error.StripeError as exc:
        await session.rollback()
        failed = await session.get(BillingPaymentOrderModel, order.id)
        if failed is not None and failed.status == "pending":
            failed.status = "failed"
            await session.commit()
        raise _stripe_failure(exc) from exc


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

    event_type = event.get("type")
    if event_type == "checkout.session.completed":
        checkout = event.get("data", {}).get("object", {}) or {}
        metadata = checkout.get("metadata", {}) or {}
        order_ref = str(metadata.get("order_ref") or "")
        if metadata.get("kind") not in {"promote", "subscription"}:
            return {"received": True}
        if not order_ref:
            logger.error("stripe.checkout.completed has no server order reference; event=%s", event.get("id", "-"))
            return {"received": True}
        result = await session.execute(
            select(BillingPaymentOrderModel)
            .where(BillingPaymentOrderModel.order_ref == order_ref)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if order is None or order.provider != "stripe":
            logger.error("stripe.checkout.completed references unknown order_ref=%s", order_ref)
            return {"received": True}
        if order.status == "applied":
            return {"received": True}
        if order.status != "pending":
            return {"received": True}
        if order.provider_ref and str(checkout.get("id") or "") != order.provider_ref:
            raise HTTPException(status_code=400, detail="Checkout session mismatch")
        if str(checkout.get("currency") or "").upper() != order.currency:
            raise HTTPException(status_code=400, detail="Payment currency mismatch")
        if _stripe_int(checkout.get("amount_total"), "amount") != order.amount_cents:
            raise HTTPException(status_code=400, detail="Payment amount mismatch")
        if str(metadata.get("user_id") or "") != order.user_id or str(metadata.get("company_id") or "") != order.company_id:
            raise HTTPException(status_code=400, detail="Payment owner mismatch")
        if order.product_kind == "promotion":
            if checkout.get("mode") != "payment" or metadata.get("kind") != "promote":
                raise HTTPException(status_code=400, detail="Wrong checkout mode")
            if (
                str(metadata.get("listing_id") or "") != str(order.listing_id)
                or str(metadata.get("tier") or "") != order.tier
                or _stripe_int(metadata.get("days"), "duration") != order.duration_days
                or checkout.get("payment_status") != "paid"
            ):
                raise HTTPException(status_code=400, detail="Promotion order metadata mismatch")
            try:
                listing_id = uuid.UUID(str(order.listing_id))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid order listing")
            listing = await session.get(ListingsModel, listing_id)
            if listing is None or str(listing.company_id) != order.company_id:
                raise HTTPException(status_code=400, detail="Listing no longer belongs to order company")
            now = datetime.now()
            base = listing.promoted_until if listing.promoted_until and listing.promoted_until > now else now
            listing.promoted_until = base + timedelta(days=int(order.duration_days or 0))
            listing.promoted_tier = order.tier
        elif order.product_kind == "subscription":
            if checkout.get("mode") != "subscription" or metadata.get("kind") != "subscription":
                raise HTTPException(status_code=400, detail="Wrong checkout mode")
            if str(metadata.get("tier") or "") != order.tier or checkout.get("payment_status") != "paid":
                raise HTTPException(status_code=400, detail="Subscription order metadata mismatch")
            company = await session.get(CompanyModel, order.company_id)
            if company is None:
                raise HTTPException(status_code=400, detail="Subscription company no longer exists")
            subscription = checkout.get("subscription")
            if isinstance(subscription, dict):
                subscription = subscription.get("id")
            if not subscription:
                raise HTTPException(status_code=400, detail="Stripe subscription ID missing")
            company.subscription_tier = order.tier
            company.stripe_subscription_id = str(subscription)
            order.stripe_subscription_id = str(subscription)
        else:
            raise HTTPException(status_code=400, detail="Unknown payment order type")
        order.provider_ref = order.provider_ref or str(checkout.get("id") or "")
        order.status = "applied"
        order.processed_at = datetime.now(UTC)
        await session.commit()
    elif event_type == "customer.subscription.updated":
        subscription = event.get("data", {}).get("object", {}) or {}
        subscription_id = str(subscription.get("id") or "")
        subscription_status = str(subscription.get("status") or "").lower()
        if subscription_id:
            order_result = await session.execute(
                select(BillingPaymentOrderModel)
                .where(
                    BillingPaymentOrderModel.provider == "stripe",
                    BillingPaymentOrderModel.product_kind == "subscription",
                    BillingPaymentOrderModel.stripe_subscription_id == subscription_id,
                    BillingPaymentOrderModel.status == "applied",
                )
                .limit(1)
            )
            order = order_result.scalar_one_or_none()
            if order is not None:
                tier = order.tier if subscription_status in {"active", "trialing"} else "free"
                await session.execute(
                    update(CompanyModel)
                    .where(
                        CompanyModel.id == order.company_id,
                        CompanyModel.stripe_subscription_id == subscription_id,
                    )
                    .values(subscription_tier=tier)
                )
                await session.commit()
    elif event_type == "customer.subscription.deleted":
        subscription = event.get("data", {}).get("object", {}) or {}
        subscription_id = str(subscription.get("id") or "")
        if subscription_id:
            result = await session.execute(
                update(CompanyModel)
                .where(CompanyModel.stripe_subscription_id == subscription_id)
                .values(subscription_tier="free", stripe_subscription_id=None)
            )
            await session.commit()
            logger.info("stripe.subscription.deleted subscription_id=%s affected=%s", subscription_id, result.rowcount)
    return {"received": True}


# ============================================================
# Stripe Subscription (FREE, AI, AI Navigácia)
# ============================================================


class _StripeSubscriptionIn(BaseModel):
    tier: str = Field(default="ai")  # "ai" alebo "ai_navigation"
    company_id: str
    success_url: str
    cancel_url: str


_STRIPE_SUBSCRIPTION_PRICES = {
    "ai": 2900,  # 29 € v centoch
    "ai_navigation": 9900,  # 99 € v centoch
}


@router.post("/stripe/subscription")
async def stripe_subscription(
    body: _StripeSubscriptionIn,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not secret:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    stripe.api_key = secret
    amount = _STRIPE_SUBSCRIPTION_PRICES.get(body.tier)
    if amount is None:
        raise HTTPException(status_code=422, detail="Unknown subscription tier")
    _validate_checkout_urls(body.success_url, body.cancel_url)
    require_company_admin(current_user, body.company_id, action="purchase subscription for")
    actor_id = _current_actor_id(current_user)
    company_result = await session.execute(
        select(CompanyModel)
        .where(CompanyModel.id == str(body.company_id))
        .with_for_update()
    )
    company = company_result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="company_not_found")
    if company.stripe_subscription_id:
        raise HTTPException(status_code=409, detail="An active Stripe subscription already exists")
    pending_result = await session.execute(
        select(BillingPaymentOrderModel)
        .where(
            BillingPaymentOrderModel.company_id == str(company.id),
            BillingPaymentOrderModel.product_kind == "subscription",
            BillingPaymentOrderModel.status == "pending",
        )
        .with_for_update()
    )
    pending_order = pending_result.scalar_one_or_none()
    if pending_order is not None:
        cutoff = datetime.now(UTC) - timedelta(minutes=30)
        created_at = pending_order.created_at
        if created_at is not None and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        if created_at is not None and created_at > cutoff:
            raise HTTPException(status_code=409, detail="A subscription checkout is already pending")
        pending_order.status = "failed"
    order = _new_order(
        provider="stripe",
        actor_id=actor_id,
        company_id=str(company.id),
        kind="subscription",
        tier=body.tier,
        amount_cents=amount,
    )
    session.add(order)
    await session.commit()
    metadata = {
        "kind": "subscription",
        "order_ref": order.order_ref,
        "tier": body.tier,
        "company_id": str(company.id),
        "user_id": actor_id,
    }
    try:
        cs = stripe.checkout.Session.create(
            mode="subscription",
            allowed_payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": amount,
                        "recurring": {"interval": "month"},
                        "product_data": {"name": f"CMEP {body.tier.upper()} (mesačné predplatné)"},
                    },
                    "quantity": 1,
                }
            ],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata=metadata,
            subscription_data={"metadata": metadata},
        )
        order.provider_ref = str(cs.id)
        await session.commit()
        return {"url": cs.url, "id": cs.id}
    except stripe.error.StripeError as exc:
        await session.rollback()
        failed = await session.get(BillingPaymentOrderModel, order.id)
        if failed is not None and failed.status == "pending":
            failed.status = "failed"
            await session.commit()
        raise _stripe_failure(exc) from exc
