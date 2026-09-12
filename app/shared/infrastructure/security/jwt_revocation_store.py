"""Token revocation store — Redis or in-memory (Termux / dev)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import settings

_jwt = settings.jwt
assert _jwt is not None, "JWT settings are not configured"
REFRESH_TOKEN_TTL_DAYS = int(str(_jwt.refresh_token_expire_days))


class _MemoryBackend:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    def _purge(self) -> None:
        now = datetime.now(UTC).timestamp()
        dead = [k for k, (_, exp) in self._store.items() if exp is not None and exp <= now]
        for k in dead:
            self._store.pop(k, None)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._purge()
        exp = None
        if ex is not None and ex > 0:
            exp = datetime.now(UTC).timestamp() + ex
        self._store[key] = (value, exp)

    async def get(self, key: str) -> str | None:
        self._purge()
        item = self._store.get(key)
        if not item:
            return None
        return item[0]

    async def exists(self, key: str) -> int:
        self._purge()
        return 1 if key in self._store else 0

    async def close(self) -> None:
        self._store.clear()


class TokenRevocationStore:
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or str(settings.redis.url)
        self._client: Any = None
        self._use_memory = (
            not getattr(settings.redis, "enabled", False)
            or self.redis_url.startswith("memory:")
            or self.redis_url in ("", "none", "disabled")
        )

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if self._use_memory:
            self._client = _MemoryBackend()
            return self._client
        try:
            import redis.asyncio as redis

            self._client = redis.from_url(self.redis_url, decode_responses=True)
            return self._client
        except Exception:
            self._client = _MemoryBackend()
            self._use_memory = True
            return self._client

    async def revoke_access_token(self, jti: str, exp: datetime) -> None:
        client = await self._get_client()
        ttl = int((exp - datetime.now(UTC)).total_seconds())
        if ttl > 0:
            await client.set(f"revoked:access:{jti}", "1", ex=ttl)

    async def revoke_refresh_token(self, jti: str, family_id: str, exp: datetime) -> None:
        client = await self._get_client()
        ttl = int((exp - datetime.now(UTC)).total_seconds())
        if ttl > 0:
            await client.set(f"revoked:refresh:{jti}", "1", ex=ttl)
            await client.set(f"revoked:family:{family_id}", "1", ex=ttl)

    async def revoke_user_tokens_after(self, subject: str, cutoff: datetime) -> None:
        client = await self._get_client()
        cutoff_utc = cutoff.astimezone(UTC)
        ttl = int(timedelta(days=REFRESH_TOKEN_TTL_DAYS).total_seconds())
        await client.set(
            f"revoked:user:{subject}:after",
            cutoff_utc.isoformat(),
            ex=ttl,
        )

    async def get_user_tokens_revoked_after(self, subject: str) -> datetime | None:
        client = await self._get_client()
        value = await client.get(f"revoked:user:{subject}:after")
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    async def is_access_token_revoked(self, jti: str) -> bool:
        client = await self._get_client()
        try:
            return await client.exists(f"revoked:access:{jti}") > 0
        except Exception:
            return False

    async def is_family_revoked(self, family_id: str) -> bool:
        client = await self._get_client()
        try:
            return await client.exists(f"revoked:family:{family_id}") > 0
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            close = getattr(self._client, "close", None)
            if close:
                await close()
            self._client = None


_revocation_store: TokenRevocationStore | None = None


def get_revocation_store() -> TokenRevocationStore:
    global _revocation_store
    if _revocation_store is None:
        _revocation_store = TokenRevocationStore()
    return _revocation_store
