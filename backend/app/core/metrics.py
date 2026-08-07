"""Monitoring a metriky."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

# Metriky
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Active HTTP requests",
)

DATABASE_CONNECTIONS = Gauge(
    "database_connections",
    "Database connections",
)

REDIS_CONNECTIONS = Gauge(
    "redis_connections",
    "Redis connections",
)


def setup_metrics() -> None:
    """Inicializácia metrík."""
    # Registrácia metrík
    pass


async def metrics_middleware(request: Request, call_next):
    """Middleware pre zber metrík."""
    start_time = time.time()
    
    # Zvýšenie aktívnych požiadaviek
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Zaznamenanie metriky
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status_code,
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(time.time() - start_time)
        
        return response
        
    finally:
        # Zníženie aktívnych požiadaviek
        ACTIVE_REQUESTS.dec()


async def metrics_endpoint(request: Request) -> Response:
    """Endpoint pre metriky."""
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )
