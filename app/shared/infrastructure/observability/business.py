"""Business observability with OpenTelemetry (optional)."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    _tracer = trace.get_tracer("cmep.business")
except ImportError:
    _tracer = None
    logger.info("OpenTelemetry not installed; observability will be no-op")


@contextmanager
def business_span(name: str, attributes: dict[str, Any] | None = None):
    """Context manager for business transaction spans."""
    if _tracer is None:
        yield None
        return
    with _tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def track_inquiry_lifecycle(inquiry_id: str, stage: str) -> None:
    """Emit a simple business event (extend with metrics later)."""
    logger.info("inquiry_lifecycle inquiry=%s stage=%s", inquiry_id, stage)