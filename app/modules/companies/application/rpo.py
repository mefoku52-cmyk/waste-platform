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


def _row_to_hit(row: dict) -> dict:
    names = row.get("fullNames") or []
    current = next((n for n in names if not n.get("validTo")), names[-1] if names else {})
    addrs = row.get("addresses") or []
    addr = next((a for a in addrs if not a.get("validTo")), addrs[0] if addrs else {})
    city = None
    mun = addr.get("municipality") if isinstance(addr, dict) else None
    if isinstance(mun, dict):
        city = mun.get("value")
    icos = row.get("identifiers") or []
    ico = None
    for item in icos:
        val = str((item or {}).get("value") or "")
        digits = "".join(ch for ch in val if ch.isdigit())
        if len(digits) == 8:
            ico = digits
            break
    activity = None
    codes = row.get("statisticalCodes") or {}
    main = codes.get("mainActivity") if isinstance(codes, dict) else None
    if isinstance(main, dict):
        activity = main.get("value")
    return {
        "ok": True,
        "exists": True,
        "ico": ico,
        "legalName": current.get("value") if isinstance(current, dict) else None,
        "city": city,
        "activity": activity,
        "reason": "found",
    }


def search_rpo(
    *,
    full_name: str | None = None,
    municipality: str | None = None,
    main_activity: str | None = None,
    only_active: bool = True,
    limit: int = 30,
) -> list[dict]:
    """Public SUSR RPO search. No API key. Does not return email."""
    params: dict[str, str] = {}
    if full_name:
        params["fullName"] = full_name.strip()
    if municipality:
        params["addressMunicipality"] = municipality.strip()
    if main_activity:
        params["mainActivity"] = main_activity.strip()
    if only_active:
        params["onlyActive"] = "true"
    if not params:
        return []
    url = f"{RPO_SEARCH}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "CMEP-RPO/1.0", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []
    rows = payload.get("results") or []
    out: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        hit = _row_to_hit(row if isinstance(row, dict) else {})
        key = str(hit.get("ico") or hit.get("legalName") or "")
        if not hit.get("legalName") or key in seen:
            continue
        seen.add(key)
        out.append(hit)
        if len(out) >= max(1, min(int(limit), 30)):
            break
    return out
