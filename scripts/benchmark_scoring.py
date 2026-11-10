#!/usr/bin/env python3
"""Reproduzierbarer scoring benchmark (studeny vs zahriaty cache).

Meria score_company_batch nad vygenerovanymi riadkami, najprv so studenou
cache (vsetky unikatne), potom so zahriatou cache (rovnake riadky opakovane).
Vystup: casy, speedup, cache_stats. Ziadne externne zavislosti okrem repo.
"""

from __future__ import annotations

import time
from uuid import uuid4

from app.modules.recommendations.application.scoring import (
    score_company_batch,
)


def _make_rows(n: int, repeat: bool = False) -> list[dict]:
    rows: list[dict] = []
    cities = ["Bratislava", "Kosice", "Presov", "Zilina", "Banska Bystrica"]
    materials = ["ocel", "drevo", "plast", "papier", "sklo", "kov"]
    for i in range(n):
        city = cities[i % len(cities)]
        material = materials[i % len(materials)]
        rows.append(
            {
                "listing_location": city + " centrum",
                "listing_material": material,
                "listing_lat": 48.1486 + i * 0.001,
                "listing_lng": 17.1077 + i * 0.001,
                "city": city if repeat else None,
                "logistics_capability": bool(i % 2),
                "event_hits": i % 4,
                "accepted_material_types": material if repeat else f"mat_{i}",
                "company_lat": 48.1486 + i * 0.001,
                "company_lng": 17.1077 + i * 0.001,
            }
        )
    return rows


def _bench(rows: list[dict], label: str) -> float:
    start = time.perf_counter()
    results = score_company_batch(rows)
    elapsed = time.perf_counter() - start
    assert len(results) == len(rows)
    print(f"{label}: {elapsed:.4f}s  ({len(rows)} riadkov)")
    return elapsed


def main() -> None:
    from app.modules.recommendations.application import scoring as scoring_mod

    n = 20_000

    # Studena cache: vsetky unikatne pary (zadne hits).
    scoring_mod._material_compat_cached.cache_clear()
    scoring_mod._city_match_cached.cache_clear()
    cold_rows = _make_rows(n, repeat=False)
    cold = _bench(cold_rows, "STUDENA cache")

    # Zahriata cache: rovnake riadky znova (vsetky hits).
    scoring_mod._material_compat_cached.cache_clear()
    scoring_mod._city_match_cached.cache_clear()
    warm_rows = _make_rows(n, repeat=True)
    _ = score_company_batch(warm_rows)  # nagriej
    warm = _bench(warm_rows, "ZAHRIATA cache")

    print()
    print(f"Speedup (zahriata/studena): {cold / warm:.2f}x")
    print(f"material cache: {scoring_mod._material_compat_cached.cache_info()}")
    print(f"city cache: {scoring_mod._city_match_cached.cache_info()}")


if __name__ == "__main__":
    main()
