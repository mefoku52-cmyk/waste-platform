"""Pytest fixtures pre waste-platform tests.

Nastavuje SQLite namiesto Postgres pre lokálne testy (Termux, CI).
"""

import os
import tempfile

_TEST_DB_DIR = os.path.join(tempfile.gettempdir(), "zyvo_ci")
# Priame priradenie (NIE setdefault): shell môže exportovať DATABASE_URL na
# Postgres — testy musia byť hermetic vždy, nie len keď env nie je nastavený.
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:////{_TEST_DB_DIR}/test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-ok"
os.environ["ENV"] = "test"
os.environ["APP_ENV"] = "test"

# Testy musia byt hermetic — ziadny realny Redis server.
# jwt_revocation_store.TokenRevocationStore pouzije _MemoryBackend,
# ak settings.redis.url zacina s "memory:".
# Tym padom 9 JWT testov funguje aj v Termuxe bez redis-server.
os.environ["REDIS_URL"] = "memory://"

# Testy musia byt hermetic — nesmu zavisiet od lokalneho `.env` ani od stavu
# Redis. Rate limiting je stavova (per-IP/per-email okna) a pod ASGI transportom
# `client_ip()` spadne na jeden zdielany bucket, takze viacero login testov v
# jednom behu by narazilo na 429 a suite by bola nespravodlivo flaky.
# Samotne spravanie rate limitera maju vlastne testy (test_rate_limit /
# test_rate_limiter). Hodnota v os.environ ma prednost pred `.env` suborom.
os.environ["RATE_LIMIT_ENABLED"] = "false"

from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_var_dir():
    # Hermetic: test DB žije v $TMPDIR (mimo repo, mimo var/).
    Path(_TEST_DB_DIR).mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_db(_ensure_var_dir):
    import asyncio

    import app.shared.infrastructure.db.register_models  # noqa: F401
    from app.shared.infrastructure.db.base import Base
    from app.shared.infrastructure.db.session import engine

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield


@pytest.fixture
async def db_session():
    """Per-test AsyncSession. Rollbackne sa po kazdom teste."""
    from app.shared.infrastructure.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
