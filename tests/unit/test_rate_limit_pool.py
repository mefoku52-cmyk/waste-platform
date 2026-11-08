"""Mock-based Redis pool tests; no live server or app startup."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError

from app.shared.infrastructure import rate_limit as rl


class TestSharedPool(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        config = SimpleNamespace(
            redis=SimpleNamespace(
                url="redis://localhost:6379/0",
                host="localhost", port=6379, db=0,
            ),
            rate_limit=SimpleNamespace(
                enabled=True, requests=10, period=60,
            ),
        )
        self.client = MagicMock()
        self.client.aclose = AsyncMock()
        for name, value in [
            ("settings", config),
            ("_redis_client", None),
            ("_mem", {}),
            ("_last_redis_warning", float("-inf")),
        ]:
            replacement = patch.object(rl, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        factory = patch.object(
            rl.Redis, "from_url", return_value=self.client,
        )
        self.factory = factory.start()
        self.addCleanup(factory.stop)

    def pipeline(self, count=1, error=None):
        pipe = MagicMock()
        pipe.execute = AsyncMock(
            return_value=[0, 1, count, True],
            side_effect=error,
        )
        context = self.client.pipeline.return_value
        context.__aenter__ = AsyncMock(return_value=pipe)
        context.__aexit__ = AsyncMock(return_value=False)
        return pipe

    async def test_concurrent_reuse(self):
        clients = await asyncio.gather(
            *(rl._client() for _ in range(100))
        )
        self.assertTrue(all(c is self.client for c in clients))
        self.factory.assert_called_once()
        self.client.ping.assert_not_called()
        self.assertEqual(
            self.factory.call_args.kwargs["max_connections"], 32,
        )

    async def test_shutdown_and_restart(self):
        await rl.init_rate_limit()
        await rl.close_rate_limit()
        await rl.close_rate_limit()
        self.client.aclose.assert_awaited_once_with(
            close_connection_pool=True,
        )
        self.assertIsNone(rl._redis_client)
        await rl.init_rate_limit()
        self.assertEqual(self.factory.call_count, 2)

    async def test_memory_backend(self):
        rl.settings.redis.url = "memory://"
        await rl.check_rate_limit("memory", limit=1)
        with self.assertRaises(HTTPException) as exc:
            await rl.check_rate_limit("memory", limit=1)
        self.assertEqual(exc.exception.status_code, 429)
        self.factory.assert_not_called()

    async def test_outage_and_recovery(self):
        self.pipeline(error=RedisConnectionError("offline"))
        with patch.object(rl.logger, "warning"):
            await rl.check_rate_limit("outage", limit=1)
            with self.assertRaises(HTTPException) as exc:
                await rl.check_rate_limit("outage", limit=1)
        self.assertEqual(exc.exception.status_code, 429)
        pipe = self.pipeline()
        await rl.check_rate_limit("recovered", limit=1)
        pipe.execute.assert_awaited_once()
        self.factory.assert_called_once()

    async def test_redis_limit_no_memory_fallback(self):
        self.pipeline(count=2)
        with self.assertRaises(HTTPException) as exc:
            await rl.check_rate_limit("redis", limit=1)
        self.assertEqual(exc.exception.status_code, 429)
        self.assertEqual(rl._mem, {})

    async def test_unique_members_at_same_time(self):
        pipe = self.pipeline()
        with patch.object(rl.time, "time", return_value=1700000000.0):
            await rl.check_rate_limit("same")
            await rl.check_rate_limit("same")
        first, second = [
            call.args[1]
            for call in pipe.zadd.call_args_list
        ]
        self.assertTrue(set(first).isdisjoint(second))

    async def test_disabled(self):
        rl.settings.rate_limit.enabled = False
        await rl.init_rate_limit()
        await rl.check_rate_limit("disabled")
        self.factory.assert_not_called()

    async def test_cancel_propagates(self):
        self.pipeline(error=asyncio.CancelledError())
        with self.assertRaises(asyncio.CancelledError):
            await rl.check_rate_limit("cancelled")
        self.assertEqual(rl._mem, {})
