"""Simple Redis (or memory) rate limiter."""

from __future__ import annotations

import time

from fastapi import HTTPException, Request

from app.core.config import settings

_mem: dict[str, list[float]] = {}


def _client():
    try:
        import redis

        host = getattr(settings.redis, "host", "localhost")
        port = getattr(settings.redis, "port", 6379)
        url = getattr(settings.redis, "url", None) or f"redis://{host}:{port}/0"
        r = redis.from_url(url, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None


def check_rate_limit(key: str, *, limit: int | None = None, period: int | None = None) -> None:
    if not settings.rate_limit.enabled:
        return
    limit = limit if limit is not None else max(5, min(settings.rate_limit.requests, 20))
    period = period if period is not None else settings.rate_limit.period
    r = _client()
    rk = f"rl:{key}"
    now = time.time()
    if r is not None:
        pipe = r.pipeline()
        pipe.zremrangebyscore(rk, 0, now - period)
        pipe.zadd(rk, {str(now): now})
        pipe.zcard(rk)
        pipe.expire(rk, period + 1)
        _, _, count, _ = pipe.execute()
        if int(count) > limit:
            raise HTTPException(status_code=429, detail="Príliš veľa pokusov. Skús neskôr.")
        return
    # memory fallback
    hits = [t for t in _mem.get(rk, []) if t > now - period]
    hits.append(now)
    _mem[rk] = hits
    if len(hits) > limit:
        raise HTTPException(status_code=429, detail="Príliš veľa pokusov. Skús neskôr.")


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"
