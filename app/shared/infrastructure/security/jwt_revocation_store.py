import json
from datetime import datetime, timezone
from typing import Any
import redis.asyncio as redis
from app.core.config import settings


class TokenRevocationStore:
    """
    Redis-based token revocation store.
    - Access tokens: revoked until expiry (short TTL)
    - Refresh tokens: revoked until family expiry
    """
    
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or str(settings.redis.url)
        self._client: redis.Redis | None = None
    
    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    async def revoke_access_token(self, jti: str, exp: datetime) -> None:
        """Revoke access token by JTI. Auto-expires when token expires."""
        client = await self._get_client()
        ttl = int((exp - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await client.setex(f"revoked:access:{jti}", ttl, "1")
    
    async def revoke_refresh_token(self, jti: str, family_id: str, exp: datetime) -> None:
        """Revoke refresh token and invalidate entire family."""
        client = await self._get_client()
        ttl = int((exp - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await client.setex(f"revoked:refresh:{jti}", ttl, "1")
            await client.setex(f"revoked:family:{family_id}", ttl, "1")
    
    async def is_access_token_revoked(self, jti: str) -> bool:
        client = await self._get_client()
        try:
            return await client.exists(f"revoked:access:{jti}") > 0
        except Exception:
            # fail-open: Redis nedostupny – neodmietaj session
            return False
    
    async def is_family_revoked(self, family_id: str) -> bool:
        """Check if entire token family is revoked (replay attack detected)."""
        client = await self._get_client()
        return await client.exists(f"revoked:family:{family_id}") > 0
    
    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


_revocation_store: TokenRevocationStore | None = None


def get_revocation_store() -> TokenRevocationStore:
    global _revocation_store
    if _revocation_store is None:
        _revocation_store = TokenRevocationStore()
    return _revocation_store
