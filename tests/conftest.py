"""Pytest fixtures pre waste-platform tests.

Nastavuje SQLite namiesto Postgres pre lokálne testy (Termux, CI).
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./var/test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-min-32-chars-long-ok")
os.environ.setdefault("ENV", "test")

from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_var_dir():
    Path("var").mkdir(exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_db(_ensure_var_dir):
    import asyncio

    import app.shared.infrastructure.db.register_models  # noqa: F401
    from app.shared.infrastructure.db.base import Base
    from app.shared.infrastructure.db.session import engine

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield
