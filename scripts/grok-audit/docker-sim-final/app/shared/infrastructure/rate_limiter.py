import math
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.shared.presentation.metrics_router import RATE_LIMIT_EXCEEDED_TOTAL


class InMemoryRateLimiter:
    def __init__(self, requests_per_window: int = 100, window_seconds: int = 60):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._storage: dict[str, deque[float]] = defaultdict(deque)

    def _key(self, request: Request) -> str:
        client = request.client.host if request.client else "unknown"
        return f"{client}:{request.url.path}"

    async def enforce(self, request: Request) -> None:
        key = self._key(request)
        now = time.time()
        queue = self._storage[key]

        # Remove expired entries
        while queue and queue[0] <= now - self.window_seconds:
            queue.popleft()

        if len(queue) >= self.requests_per_window:
            RATE_LIMIT_EXCEEDED_TOTAL.labels(route=request.url.path).inc()
            retry_after = max(1, math.ceil(queue[0] + self.window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

        queue.append(now)
