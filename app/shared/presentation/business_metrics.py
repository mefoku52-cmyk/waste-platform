"""Business-level Prometheus counters for lead-finder pipeline.

Exposes named counters that the metrics_router aggregates into the
text-based /metrics endpoint. Modules increment these on the happy
path so we can chart discovery / draft / send volumes over time.

All counters are idempotent at import time. Import this module once
from the entry points that need to record metrics; do not redefine
counters in multiple places (prometheus_client raises on duplicate
registration).
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

DISCOVERY_TOTAL = Counter(
    "cmep_discovery_total",
    "Companies discovered per source",
    ["source"],  # zs_category | rpo | backfill
)

DISCOVERY_SAVED_TOTAL = Counter(
    "cmep_discovery_saved_total",
    "New outreach candidates saved",
    ["source"],
)

DRAFTS_TOTAL = Counter(
    "cmep_drafts_total",
    "Drafts generated",
    ["result"],  # ok | failed | skipped
)

SEND_TOTAL = Counter(
    "cmep_send_total",
    "Emails sent",
    ["result"],  # ok | failed
)

BOUNCE_TOTAL = Counter(
    "cmep_bounce_total",
    "Provider-reported bounces (from Resend error messages)",
)

AUTO_APPROVE_TOTAL = Counter(
    "cmep_auto_approve_total",
    "Candidates approved automatically",
    ["result"],  # approved | skipped_no_email | skipped_junk | skipped_invalid
)

PIPELINE_DURATION = Histogram(
    "cmep_pipeline_duration_seconds",
    "Duration of pipeline stages",
    ["stage"],  # zs_discovery | draft_batch | send_batch
    buckets=(0.5, 1, 5, 15, 30, 60, 120, 300, 600, 1800),
)


__all__ = [
    "AUTO_APPROVE_TOTAL",
    "BOUNCE_TOTAL",
    "DISCOVERY_SAVED_TOTAL",
    "DISCOVERY_TOTAL",
    "DRAFTS_TOTAL",
    "PIPELINE_DURATION",
    "SEND_TOTAL",
]
