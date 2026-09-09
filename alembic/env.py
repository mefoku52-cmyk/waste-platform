from logging.config import fileConfig
import os

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.shared.infrastructure.db.base import Base

# Import all SQLAlchemy models so Base.metadata is complete.
from app.modules.users.infrastructure import models as users_models  # noqa: F401
from app.modules.auth.infrastructure import models as auth_models  # noqa: F401
from app.modules.companies.infrastructure import models as companies_models  # noqa: F401
from app.modules.company_memberships.infrastructure import models as memberships_models  # noqa: F401
from app.modules.listings.infrastructure import models as listings_models  # noqa: F401
from app.modules.inquiries.infrastructure import models as inquiries_models  # noqa: F401
from app.modules.documents.infrastructure import models as documents_models  # noqa: F401
from app.modules.compliance.infrastructure import models as compliance_models  # noqa: F401
from app.modules.notifications.infrastructure import models as notifications_models  # noqa: F401
from app.modules.analytics.infrastructure import models as analytics_models  # noqa: F401
from app.modules.admin.infrastructure import models as admin_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


def run_migrations_offline() -> None:
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = create_async_engine(
        get_database_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
