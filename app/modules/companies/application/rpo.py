"""Lookup ICO in official SUSR RPO. No API key. CC-BY 4.0 SUSR."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RPO_SEARCH = "https://api.statistics.sk/rpo/v1/search"


def normalize_ico(raw: str | None) -> str:
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    return digits.zfill(8) if digits else ""


def lookup_ico(raw: str | None) -> dict:
    ico = normalize_ico(raw)
    if len(ico) != 8:
        return {
            "ok": False,
            "exists": False,
            "ico": ico or None,
            "legalName": None,
            "city": None,
            "reason": "ico_invalid",
        }
    url = f"{RPO_SEARCH}?{urlencode({'identifier': ico})}"
    req = Request(url, headers={"User-Agent": "CMEP-RPO/1.0", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        return {
            "ok": False,
            "exists": False,
            "ico": ico,
            "legalName": None,
            "city": None,
            "reason": f"http_{exc.code}",
        }
    except (URLError, TimeoutError, json.JSONDecodeError):
        return {
            "ok": False,
            "exists": False,
            "ico": ico,
            "legalName": None,
            "city": None,
            "reason": "rpo_unavailable",
        }

    rows = payload.get("results") or []
    if not rows:
        return {
            "ok": True,
            "exists": False,
            "ico": ico,
            "legalName": None,
            "city": None,
            "reason": "not_found",
        }

    row = rows[0]
    names = row.get("fullNames") or []
    current = next((n for n in names if not n.get("validTo")), names[-1] if names else {})
    addrs = row.get("addresses") or []
    addr = next((a for a in addrs if not a.get("validTo")), addrs[0] if addrs else {})
    city = (
        ((addr.get("municipality") or {}).get("value"))
        if isinstance(addr.get("municipality"), dict)
        else None
    )
    return {
        "ok": True,
        "exists": True,
        "ico": ico,
        "legalName": current.get("value"),
        "city": city,
        "reason": "found",
    }
