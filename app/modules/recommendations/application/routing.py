"""Live geocode + OSRM route + fuel cost. No deal is created."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OSRM = "https://router.project-osrm.org/route/v1/driving"
UA = "CMEP-waste-platform/1.0 (route-calculator)"
VIGNETTE_EUR = 8.1


def _get_json(url: str) -> dict | list:
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise ValueError(exc.read().decode("utf-8", "replace")[:200] or str(exc)) from exc


def geocode(query: str) -> dict:
    q = (query or "").strip()
    if len(q) < 2:
        raise ValueError("Location is too short")
    url = NOMINATIM + "?" + urlencode({"q": q, "format": "json", "limit": 1})
    data = _get_json(url)
    if not isinstance(data, list) or not data:
        raise ValueError("Location not found: " + q)
    hit = data[0]
    return {
        "label": hit.get("display_name") or q,
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
    }


def osrm_route(origin: dict, dest: dict, *, exclude_motorway: bool = False) -> dict:
    path = f"{origin['lon']},{origin['lat']};{dest['lon']},{dest['lat']}"
    extra = "&exclude=motorway" if exclude_motorway else ""
    url = f"{OSRM}/{path}?overview=false&alternatives=false{extra}"
    data = _get_json(url)
    if not isinstance(data, dict) or data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("Route not found")
    route = data["routes"][0]
    meters = float(route["distance"])
    seconds = float(route["duration"])
    return {
        "distanceKm": round(meters / 1000.0, 1),
        "durationMin": round(seconds / 60.0),
        "usesMotorway": not exclude_motorway,
    }


def fuel_cost(
    *, distance_km: float, consumption: float, fuel_price: float, roundtrip: bool
) -> dict:
    km = distance_km * (2.0 if roundtrip else 1.0)
    liters = km * consumption / 100.0
    cost = liters * fuel_price
    return {
        "chargeableKm": round(km, 1),
        "fuelLiters": round(liters, 1),
        "fuelEur": round(cost, 2),
        "roundtrip": roundtrip,
        "consumptionLPer100km": consumption,
        "fuelPriceEur": fuel_price,
    }


def calculate_route(
    *,
    origin_text: str,
    destination_text: str,
    consumption: float = 28.0,
    fuel_price: float = 1.49,
    roundtrip: bool = False,
) -> dict:
    try:
        origin = geocode(origin_text)
        dest = geocode(destination_text)
        highway = osrm_route(origin, dest, exclude_motorway=False)
        try:
            local = osrm_route(origin, dest, exclude_motorway=True)
        except ValueError:
            local = None
    except (URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(str(exc) or "Routing failed") from exc

    options = []
    for route, kind, extra in (
        (highway, "highway", VIGNETTE_EUR),
        (local, "no_highway", 0.0),
    ):
        if route is None:
            continue
        fuel = fuel_cost(
            distance_km=route["distanceKm"],
            consumption=consumption,
            fuel_price=fuel_price,
            roundtrip=roundtrip,
        )
        options.append(
            {
                "kind": kind,
                "label": "Dialnica + znamka" if kind == "highway" else "Bez dialnice",
                "distanceKm": route["distanceKm"],
                "durationMin": route["durationMin"],
                "fuel": fuel,
                "extraEur": extra,
                "totalEur": round(fuel["fuelEur"] + extra, 2),
            }
        )
    options.sort(key=lambda row: (row["totalEur"], row["durationMin"]))
    best = options[0]
    return {
        "origin": origin,
        "destination": dest,
        "distanceKm": best["distanceKm"],
        "durationMin": best["durationMin"],
        "fuel": best["fuel"],
        "bestKind": best["kind"],
        "options": options,
        "mapUrl": (
            "https://www.google.com/maps/dir/"
            + str(origin["lat"])
            + ","
            + str(origin["lon"])
            + "/"
            + str(dest["lat"])
            + ","
            + str(dest["lon"])
        ),
        "provider": "nominatim+osrm",
    }


def search_carriers(near: str) -> list[dict]:
    q = "doprava " + (near or "").strip()
    url = NOMINATIM + "?" + urlencode({"q": q, "format": "json", "limit": 8})
    try:
        data = _get_json(url)
    except (URLError, TimeoutError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    items = []
    for hit in data:
        items.append(
            {
                "name": hit.get("display_name") or "Dopravca",
                "lat": float(hit["lat"]),
                "lon": float(hit["lon"]),
                "osmId": str(hit.get("osm_id") or ""),
                "source": "openstreetmap",
            }
        )
    return items
