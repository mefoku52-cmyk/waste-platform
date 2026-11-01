"""Deterministicka Comparator modelovych vysledkov.

Porovnava dva ModelResponse objekty deterministicky, označi rozpor
poskytuje informacie o povode dôkazov (adapter, čas, režim, hash).
Nevyžaduje žiadne API kľúče ani sieťové volania.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .logging_safe import redact_any
from .model_adapter import ModelResponse


@dataclass(frozen=True)
class ComparisonEvidence:
    """Povod dôkazu z jednej modelovej odpovede."""

    adapter: str
    timestamp: str
    mode: str
    available: bool
    result_hash: str | None
    error: str | None


@dataclass(frozen=True)
class ComparisonResult:
    """Vysledok deterministického porovnania dvoch ModelResponse."""

    match: bool
    discrepancies: list[str]
    evidence_a: ComparisonEvidence
    evidence_b: ComparisonEvidence
    compared_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def _evidence(response: ModelResponse) -> ComparisonEvidence:
    """Vytvori ComparisonEvidence z ModelResponse."""
    result_hash = None
    if response.result:
        result_hash = hashlib.sha256(response.result.encode("utf-8")).hexdigest()
    return ComparisonEvidence(
        adapter=response.adapter,
        timestamp=response.timestamp,
        mode=response.mode,
        available=response.available,
        result_hash=result_hash,
        error=response.error,
    )


def _discrepancies(a: ModelResponse, b: ModelResponse) -> list[str]:
    """Vrati zoznam rozpolov medzi dvemi ModelResponse (deterministicky, zoradene)."""
    diffs: list[str] = []
    if a.adapter != b.adapter:
        diffs.append(f"adapter: {a.adapter} != {b.adapter}")
    if a.result != b.result:
        diffs.append("result")
    if a.deterministic != b.deterministic:
        diffs.append(f"deterministic: {a.deterministic} != {b.deterministic}")
    if a.mode != b.mode:
        diffs.append(f"mode: {a.mode} != {b.mode}")
    if a.available != b.available:
        diffs.append(f"available: {a.available} != {b.available}")
    if a.error != b.error:
        diffs.append(f"error: {a.error} != {b.error}")
    if a.metadata != b.metadata:
        diffs.append("metadata")
    return sorted(diffs)


def compare(a: ModelResponse, b: ModelResponse) -> ComparisonResult:
    """Porovnava dva ModelResponse deterministicky.

    - match: True ak su odpovede identické (podla vsetkých porovnateľných polí).
    - discrepancies: zoradený zoznam lišiacich sa polí.
    - evidence_a / evidence_b: pôvod dôkazov pre obe odpovede.
    """
    discrepancies = _discrepancies(a, b)
    return ComparisonResult(
        match=len(discrepancies) == 0,
        discrepancies=discrepancies,
        evidence_a=_evidence(a),
        evidence_b=_evidence(b),
    )


def compare_adapter_outputs(
    responses: dict[str, ModelResponse],
) -> dict[str, Any]:
    """Porovnava vystupy z viacerých adapterov proti prvému ako referencii.

    Vrati slovník s výsledkami porovnania, inkluzívne celkový stav zhody
    a evidence pre každú dvojicu. Deterministické – rovnaký vstup dava
    rovnaký výstup.
    """
    if not responses:
        return {
            "all_match": True,
            "reference": None,
            "comparisons": {},
            "evidence": {},
        }

    adapter_names = sorted(responses.keys())
    reference_name = adapter_names[0]
    reference = responses[reference_name]

    comparisons: dict[str, ComparisonResult] = {}
    evidence: dict[str, ComparisonEvidence] = {}

    all_match = True
    for name in adapter_names[1:]:
        result = compare(reference, responses[name])
        comparisons[name] = result
        evidence[name] = result.evidence_b
        if not result.match:
            all_match = False

    evidence[reference_name] = _evidence(reference)

    return {
        "all_match": all_match,
        "reference": reference_name,
        "comparisons": {
            name: {
                "match": r.match,
                "discrepancies": r.discrepancies,
                "compared_at": r.compared_at,
            }
            for name, r in comparisons.items()
        },
        "evidence": {
            name: {
                "adapter": e.adapter,
                "timestamp": e.timestamp,
                "mode": e.mode,
                "available": e.available,
                "result_hash": e.result_hash,
                "error": redact_any(e.error),
            }
            for name, e in evidence.items()
        },
    }
