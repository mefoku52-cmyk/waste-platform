"""Example registration of business commands on the idempotent bus.

This file demonstrates how existing services would be wrapped.
Do not import this in production until fully integrated.
"""

from __future__ import annotations

from typing import Any

from app.shared.infrastructure.commands.bus import command_bus


async def _create_inquiry_handler(payload: dict[str, Any]) -> dict[str, Any]:
    # In full impl this would call the real InquiryService
    return {"inquiry_id": "placeholder", "status": "created"}


async def _publish_listing_handler(payload: dict[str, Any]) -> dict[str, Any]:
    return {"listing_id": payload.get("listing_id"), "status": "published"}


def register_business_commands() -> None:
    command_bus.register("create_inquiry", _create_inquiry_handler)
    command_bus.register("publish_listing", _publish_listing_handler)
    command_bus.register("promote_listing", _publish_listing_handler)  # placeholder