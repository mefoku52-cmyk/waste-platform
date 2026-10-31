"""Validation for client-side (frontend) agent actions.

Client actions are executed by the browser, not by the backend. The backend must
still guarantee that only explicitly defined actions with safe arguments are
handed to the frontend dispatcher, so this module is the single source of truth
for the client-action allowlist and its argument validation.

Validation rules:
* only names from ``CLIENT_ACTION_NAMES`` are accepted (no unknown actions);
* identifiers are restricted to a safe character set (no path traversal);
* ``navigate`` only accepts internal relative paths (no scheme, host, ``..``);
* form fields and toast levels are explicit allowlists;
* values are scalar and length-bounded.
"""

from __future__ import annotations

import re
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.modules.agent_platform.infrastructure.tools.tool_schemas import (
    CLIENT_ACTION_NAMES,
)

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

_TOAST_LEVELS = frozenset({"info", "success", "warning", "error"})

_FORM_FIELDS = frozenset(
    {
        # Listing form
        "title",
        "description",
        "materialType",
        "quantity",
        "unit",
        "location",
        "price",
        "currency",
        "condition",
        "companyId",
        "imageUrl",
        # Company form
        "entityType",
        "legalName",
        "tradingName",
        "registrationNumber",
        "vatIdentifier",
        "companyType",
        "countryCode",
        "addressLine1",
        "city",
        "postalCode",
        "email",
        "phone",
    }
)
_NUMERIC_FIELDS = frozenset({"quantity", "price"})
_NO_ARG_ACTIONS = frozenset(
    {
        "open_new_listing",
        "open_listings_list",
        "open_companies",
        "open_dashboard",
        "open_inquiries",
        "open_new_company",
        "open_documents",
        "open_new_document",
        "open_chat",
        "open_settings",
        "open_transport",
        "open_subscription",
        "open_marketplace",
        "open_admin",
        "open_transport",
        "open_subscription",
        "open_marketplace",
    }
)

_MAX_TEXT_LENGTH = 2000
_MAX_MESSAGE_LENGTH = 500
_MAX_URL_LENGTH = 200


@dataclass(frozen=True, slots=True)
class ClientActionValidation:
    """Result of validating a single client action."""

    valid: bool
    arguments: Mapping[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


def _invalid(code: str, message: str) -> ClientActionValidation:
    return ClientActionValidation(valid=False, error_code=code, error_message=message)


def _valid(arguments: Mapping[str, Any]) -> ClientActionValidation:
    return ClientActionValidation(valid=True, arguments=dict(arguments))


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool))


def _validate_fill_form_field(arguments: Mapping[str, Any]) -> ClientActionValidation:
    field_name = arguments.get("field")
    if not isinstance(field_name, str) or field_name not in _FORM_FIELDS:
        return _invalid(
            "client_field_not_allowed",
            "field is not an allowed form field",
        )
    if "value" not in arguments:
        return _invalid("client_missing_value", "value is required")
    value = arguments["value"]
    if not _is_scalar(value):
        return _invalid("client_invalid_value", "value must be a scalar")
    if field_name in _NUMERIC_FIELDS:
        if isinstance(value, bool):
            return _invalid("client_invalid_value", "value must be numeric")
        if isinstance(value, str) and not _NUMERIC_RE.match(value.strip()):
            return _invalid("client_invalid_value", "value must be numeric")
    if isinstance(value, str) and len(value) > _MAX_TEXT_LENGTH:
        return _invalid("client_value_too_long", "value is too long")
    return _valid({"field": field_name, "value": value})


def _validate_highlight_field(arguments: Mapping[str, Any]) -> ClientActionValidation:
    field_name = arguments.get("field")
    if not isinstance(field_name, str) or field_name not in _FORM_FIELDS:
        return _invalid(
            "client_field_not_allowed",
            "field is not an allowed form field",
        )
    return _valid({"field": field_name})


def _validate_show_toast(arguments: Mapping[str, Any]) -> ClientActionValidation:
    message = arguments.get("message")
    if not isinstance(message, str) or not message.strip():
        return _invalid("client_invalid_message", "message must be a non-empty string")
    if len(message) > _MAX_MESSAGE_LENGTH:
        return _invalid("client_message_too_long", "message is too long")
    level = arguments.get("level", "info")
    if level not in _TOAST_LEVELS:
        return _invalid("client_invalid_level", "level is not allowed")
    return _valid({"message": message, "level": level})


def _validate_navigate(arguments: Mapping[str, Any]) -> ClientActionValidation:
    url = arguments.get("url")
    if not isinstance(url, str):
        return _invalid("client_invalid_path", "url must be a string")
    url = url.strip()
    if not url.startswith("/") or url.startswith("//"):
        return _invalid(
            "client_external_path_blocked",
            "url must be an internal relative path",
        )
    decoded = urllib.parse.unquote(url)
    if (
        "\\" in url
        or ":" in url
        or "\\" in decoded
        or ":" in decoded
        or ".." in decoded
        or any(ord(ch) < 32 for ch in url)
        or len(url) > _MAX_URL_LENGTH
    ):
        return _invalid("client_unsafe_path", "url is not a safe internal path")
    return _valid({"url": url})


def _validate_open_with_id(
    arguments: Mapping[str, Any],
    key: str,
) -> ClientActionValidation:
    value = arguments.get(key)
    if not isinstance(value, str) or not _SAFE_ID_RE.match(value):
        return _invalid("client_invalid_id", f"{key} must be a safe identifier")
    return _valid({key: value})


def validate_client_action(
    tool_name: str,
    arguments: Mapping[str, Any] | None,
) -> ClientActionValidation:
    """Validate a client action name and its arguments.

    Unknown actions and unsafe arguments are rejected so they are never handed
    to the frontend dispatcher.
    """
    if tool_name not in CLIENT_ACTION_NAMES:
        return _invalid(
            "client_unknown_action",
            f"'{tool_name}' is not an allowed client action",
        )

    args: Mapping[str, Any] = arguments or {}

    if tool_name == "fill_form_field":
        return _validate_fill_form_field(args)
    if tool_name == "highlight_field":
        return _validate_highlight_field(args)
    if tool_name == "show_toast":
        return _validate_show_toast(args)
    if tool_name == "navigate":
        return _validate_navigate(args)
    if tool_name == "open_listing":
        return _validate_open_with_id(args, "listing_id")
    if tool_name == "open_company":
        return _validate_open_with_id(args, "company_id")
    if tool_name in _NO_ARG_ACTIONS:
        return _valid({})

    return _invalid(
        "client_unknown_action",
        f"'{tool_name}' is not an allowed client action",
    )
