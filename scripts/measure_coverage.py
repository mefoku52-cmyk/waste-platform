#!/usr/bin/env python3
"""Measure email coverage of lookup_public_email on a fixed sample of leads.

Run on three code revisions (baseline, after fix A+B, after 1.2) with the
SAME sample, so numbers are comparable.

Preparing input (leads.json), one option:

    psql "$DATABASE_URL" -At -F '\t' -c "
        SELECT id, company_name, coalesce(city,''), coalesce(ico,'')
        FROM outreach_candidates
        WHERE company_name IS NOT NULL
        ORDER BY id LIMIT 100" > leads.tsv
    # then convert TSV -> JSON

Or prepare the JSON manually:

    [
      {"id": "...", "company_name": "...", "city": "...", "ico": "..."},
      ...
    ]

Usage:
    python scripts/measure_coverage.py --input leads.json --tag baseline
    python scripts/measure_coverage.py --input leads.json --tag after-fix
    python scripts/measure_coverage.py --input leads.json --tag after-1.2

Output: one JSON file per tag, e.g. baseline.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.modules.lead_finder.application.services.directory_lookup import (
    lookup_public_email,
)


def load_leads(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"{path} must be a JSON list of leads")
    return data


def measure(leads: list[dict], tag: str) -> dict:
    started_all = time.monotonic()
    items: list[dict] = []

    for index, lead in enumerate(leads, 1):
        company = (lead.get("company_name") or "").strip()
        city = lead.get("city") or None
        ico = lead.get("ico") or None

        started = time.monotonic()
        error: str | None = None
        email: str | None = None

        try:
            email = lookup_public_email(company, city=city, ico=ico)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        elapsed_ms = int((time.monotonic() - started) * 1000)

        items.append(
            {
                "id": lead.get("id"),
                "company_name": company,
                "email": email,
                "elapsed_ms": elapsed_ms,
                "error": error,
            }
        )

        print(
            f"[{index:>3}/{len(leads)}] {(email or '-'):<40} {company[:40]:<40} ({elapsed_ms} ms)",
            flush=True,
        )

    hits = sum(1 for item in items if item["email"])
    total = len(items)
    coverage_pct = round((hits / total) * 100, 2) if total else 0.0

    return {
        "tag": tag,
        "measured_at": datetime.now(UTC).isoformat(),
        "total": total,
        "hits": hits,
        "coverage_pct": coverage_pct,
        "elapsed_s": round(time.monotonic() - started_all, 1),
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="leads.json")
    parser.add_argument("--tag", required=True, help="output label, e.g. baseline")
    parser.add_argument("--output", type=Path, help="output JSON (default <tag>.json)")
    args = parser.parse_args()

    leads = load_leads(args.input)
    if not leads:
        raise SystemExit("input contains zero leads")

    result = measure(leads, args.tag)
    output = args.output or Path(f"{args.tag}.json")
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(f"=== {args.tag} ===")
    print(f"total    : {result['total']}")
    print(f"hits     : {result['hits']}")
    print(f"coverage : {result['coverage_pct']} %")
    print(f"elapsed  : {result['elapsed_s']} s")
    print(f"output   : {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
