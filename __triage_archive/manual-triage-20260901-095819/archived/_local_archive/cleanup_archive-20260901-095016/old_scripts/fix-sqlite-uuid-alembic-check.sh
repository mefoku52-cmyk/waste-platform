#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROJECT="$HOME/waste-platform"
cd "$PROJECT"

cp -av migrations/env.py "$HOME/waste-platform-backups/env.py.$(date +%Y%m%d_%H%M%S).bak"

cat > migrations/env.py <<'PYEOF'
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.shared.infrastructure.db.base import Base
import app.shared.infrastructure.db.register_models  # noqa: F401

try:
    from app.shared.config import settings
except Exception:
    from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = getattr(getattr(settings, "database", settings), "async_url", None)
if not database_url:
    raise RuntimeError("Cannot resolve runtime database async_url from application settings.")

config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
target_metadata = Base.metadata


def _is_uuidish(type_obj) -> bool:
    if type_obj is None:
        return False
    name = type(type_obj).__name__.lower()
    text = str(type_obj).lower()
    return "uuid" in name or "uuid" in text


def _is_sqlite_numericish(type_obj) -> bool:
    if type_obj is None:
        return False
    name = type(type_obj).__name__.lower()
    text = str(type_obj).lower()
    return "numeric" in name or "numeric" in text


def custom_compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    dialect_name = context.dialect.name

    if dialect_name == "sqlite":
        if _is_sqlite_numericish(inspected_type) and _is_uuidish(metadata_type):
            return False

    return None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=custom_compare_type,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=custom_compare_type,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
PYEOF

echo "===== ALEMBIC CURRENT ====="
alembic current || true

echo
echo "===== ALEMBIC CHECK ====="
alembic check || true

echo
echo "===== SQLITE TABLES ====="
python - <<'PY'
import sqlite3
con = sqlite3.connect("var/cmep.db")
rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for row in rows:
    print(row[0])
con.close()
PY
