"""Tests for business metrics + scheduler alerts + ready endpoint."""

from __future__ import annotations

from app.shared.presentation import business_metrics as bm


def test_all_counters_exist():
    assert bm.DISCOVERY_TOTAL is not None
    assert bm.DISCOVERY_SAVED_TOTAL is not None
    assert bm.DRAFTS_TOTAL is not None
    assert bm.SEND_TOTAL is not None
    assert bm.BOUNCE_TOTAL is not None
    assert bm.AUTO_APPROVE_TOTAL is not None
    assert bm.PIPELINE_DURATION is not None


def test_counters_have_expected_labels():
    # DRAFTS_TOTAL has 'result' label
    labels = bm.DRAFTS_TOTAL._labelnames
    assert "result" in labels

    assert "source" in bm.DISCOVERY_TOTAL._labelnames
    assert "stage" in bm.PIPELINE_DURATION._labelnames


def test_counter_increments_do_not_raise():
    """Sanity check that label patterns used in code are valid."""
    bm.DISCOVERY_TOTAL.labels(source="zs_category").inc()
    bm.DISCOVERY_SAVED_TOTAL.labels(source="zs_category").inc()
    bm.DRAFTS_TOTAL.labels(result="ok").inc()
    bm.DRAFTS_TOTAL.labels(result="failed").inc()
    bm.SEND_TOTAL.labels(result="ok").inc()
    bm.SEND_TOTAL.labels(result="failed").inc()
    bm.AUTO_APPROVE_TOTAL.labels(result="approved").inc()
    bm.PIPELINE_DURATION.labels(stage="zs_discovery").observe(1.5)


def test_ready_endpoint_registered():
    from app.main import app

    schema = app.openapi()
    assert "/ready" in schema["paths"]
    assert "get" in schema["paths"]["/ready"]


def test_summary_endpoint_registered():
    from app.main import app

    schema = app.openapi()
    assert "/api/v1/admin/metrics/summary" in schema["paths"]


def test_scheduler_alert_helper_importable():
    from app.shared.infrastructure.scheduler import _notify_scheduler_failure

    assert callable(_notify_scheduler_failure)
