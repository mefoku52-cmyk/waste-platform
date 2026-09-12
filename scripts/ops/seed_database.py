import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from app.modules.users.infrastructure.models import UserModel
from app.shared.application.passwords import PasswordService
from app.shared.infrastructure.db.base import Base
from app.shared.infrastructure.db.register_models import *
from app.shared.infrastructure.db.session import SessionLocal, engine


async def init():
    print("   [DB] Vytváram tabuľky...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   [DB] Tabuľky hotové")

    async with SessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.email == "admin@cmep.dev")
        )
        if result.scalar_one_or_none():
            print("   [DB] Admin už existuje")
            return

        ps = PasswordService()
        admin = UserModel(
            id="00000000-0000-0000-0000-000000000001",
            status="active",
            email="admin@cmep.dev",
            password_hash=ps.hash_password("Admin123!"),
            first_name="System",
            last_name="Admin",
            display_name="Administrator",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(admin)
        await session.commit()
        print("   [DB] Admin vytvorený: admin@cmep.dev / Admin123!")


if __name__ == "__main__":
    asyncio.run(init())
