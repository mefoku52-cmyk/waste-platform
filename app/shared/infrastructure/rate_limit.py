"""Simple Redis (or memory) rate limiter."""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import HTTPException, Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)
_mem: dict[str, list[float]] = {}
_redis_client: Redis | None = None
_last_redis_warning = float("-inf")


def _warn_redis_unavailable(exc: Exception) -> None:
    global _last_redis_warning
    now = time.monotonic()
    if now - _last_redis_warning >= 60:
        logger.warning(
            "Rate limiter Redis unavailable (%s); "
            "using process-local memory fallback",
            type(exc).__name__,
        )
        _last_redis_warning = now


async def _client() -> Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    host = getattr(settings.redis, "host", "localhost")
    port = getattr(settings.redis, "port", 6379)
    db = getattr(settings.redis, "db", 0)
    url = (
        getattr(settings.redis, "url", None)
        or f"redis://{host}:{port}/{db}"
    )
    if url.startswith("memory:"):
        return None
    try:
        _redis_client = Redis.from_url(
            url,
            decode_responses=True,
            max_connections=32,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
            health_check_interval=30,
        )
    except (ValueError, RedisError) as exc:
        _warn_redis_unavailable(exc)
        return None
    return _redis_client


async def init_rate_limit() -> None:
    if settings.rate_limit.enabled:
        await _client()


async def close_rate_limit() -> None:
    global _redis_client
    client, _redis_client = _redis_client, None
    if client is not None:
        await client.aclose(close_connection_pool=True)


async def check_rate_limit(
    key: str, *, limit: int | None = None, period: int | None = None
) -> None:
    if not settings.rate_limit.enabled:
        return
    limit = limit if limit is not None else max(5, min(settings.rate_limit.requests, 20))
    period = period if period is not None else settings.rate_limit.period
    r = await _client()
    rk = f"rl:{key}"
    now = time.time()
    if r is not None:
        try:
            async with r.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(rk, 0, now - period)
                pipe.zadd(rk, {uuid4().hex: now})
                pipe.zcard(rk)
                pipe.expire(rk, period + 1)
                _, _, count, _ = await pipe.execute()
        except RedisError as exc:
            _warn_redis_unavailable(exc)
        else:
            if int(count) > limit:
                raise HTTPException(
                    status_code=429,
                    detail="Príliš veľa pokusov. Skús neskôr.",
                )
            return
    # memory fallback
    hits = [t for t in _mem.get(rk, []) if t > now - period]
    hits.append(now)
    _mem[rk] = hits
    if len(hits) > limit:
        raise HTTPException(status_code=429, detail="Príliš veľa pokusov. Skús neskôr.")


def client_ip(request: Request) -> str:
    """Vrati realnu IP klienta bezpecne za Cloudflare/proxy.

    Poradie priority:
    1. CF-Connecting-IP — Cloudflare ho prepise realnou IP, klient ho
       nemoze podvrhnut.
    2. X-Real-IP — alternativa niektorych proxy.
    3. POSLEDNY prvok X-Forwarded-For — za jednym proxy je to realna IP
       klienta; klient moze append-nut falosne hodnoty na zaciatok, preto
       NEBIERAME PRVY prvok (bezpecnostna chyba najdena v KROKU 4 round 2).
    4. request.client.host ako fallback.
    """
    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()

    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            # POSLEDNY prvok = najblizsi proxy k nam = realna IP klienta.
            return parts[-1]

    if request.client:
        return request.client.host or "unknown"
    return "unknown"
