from fastapi import APIRouter, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

router = APIRouter(tags=["metrics"])

HTTP_REQUESTS_TOTAL = Counter(
    "app_http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

AUTH_FAILURES_TOTAL = Counter(
    "app_auth_failures_total",
    "Authentication failures total",
)

RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "app_rate_limit_exceeded_total",
    "Rate limit exceeded total",
    ["route"],
)


def _allowed_hosts() -> set[str]:
    from app.core.config import settings

    raw = settings.METRICS_ALLOWED_IPS
    return {item.strip() for item in raw.split(",") if item.strip()}


def _is_internal_metrics_request(request: Request) -> bool:
    client_host = request.client.host if request.client else ""
    forwarded_for = request.headers.get("x-forwarded-for", "")
    forwarded_host = forwarded_for.split(",")[0].strip() if forwarded_for else ""
    candidates = {client_host, forwarded_host}
    candidates.discard("")
    return any(host in _allowed_hosts() for host in candidates)


@router.get("/metrics", include_in_schema=False)
async def metrics(request: Request) -> Response:
    from app.core.config import settings

    enabled = settings.ENABLE_METRICS
    if not enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not _is_internal_metrics_request(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Metrics are internal only"
        )
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
