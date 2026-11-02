"""Webhook delivery service with exponential backoff and DLQ."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx

from app.modules.webhooks.domain.models import WebhookDelivery, WebhookEndpoint, WebhookEventType
from app.modules.webhooks.infrastructure.signing import sign_payload

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 8
BACKOFF_BASE = 2


class WebhookDeliveryService:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def deliver(self, endpoint: WebhookEndpoint, event_type: WebhookEventType, payload: dict[str, Any]) -> WebhookDelivery:
        delivery = WebhookDelivery(
            id=uuid4(),
            endpoint_id=endpoint.id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempts=0,
            created_at=datetime.now(UTC),
        )
        # In full impl this would persist and enqueue
        await self._attempt(endpoint, delivery)
        return delivery

    async def _attempt(self, endpoint: WebhookEndpoint, delivery: WebhookDelivery) -> None:
        delivery.attempts += 1
        signature, ts = sign_payload(endpoint.secret, delivery.payload)
        headers = {
            "X-CMEP-Signature": signature,
            "X-CMEP-Timestamp": str(ts),
            "X-CMEP-Event": delivery.event_type.value,
            "Content-Type": "application/json",
        }
        try:
            resp = await self._client.post(str(endpoint.url), json=delivery.payload, headers=headers)
            if 200 <= resp.status_code < 300:
                delivery.status = "delivered"
                return
            delivery.last_error = f"HTTP {resp.status_code}"
        except Exception as exc:
            delivery.last_error = str(exc)

        if delivery.attempts >= MAX_ATTEMPTS:
            delivery.status = "dead_letter"
        else:
            delivery.status = "failed"
            delay = BACKOFF_BASE ** delivery.attempts
            delivery.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)