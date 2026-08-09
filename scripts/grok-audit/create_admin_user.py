import asyncio
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, "/data/data/com.termux/files/home/waste-platform")

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.modules.users.infrastructure.models import UserModel

DATABASE_URL = "postgresql+asyncpg://u0_a388@localhost:5432/cmep"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL = "admin@cmep-bootstrap.dev"
PASSWORD = "Bootstrap-Admin-2026!"

async def main():
    engine = create_async_engine(DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        now = datetime.now(timezone.utc)
        user = UserModel(
            id=str(uuid.uuid4()),
            status="active",
            email=EMAIL,
            password_hash=pwd_context.hash(PASSWORD),
            first_name="Bootstrap",
            last_name="Admin",
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        await session.commit()
        print(f"OK: vytvoreny user id={user.id}, email={user.email}")
    await engine.dispose()

asyncio.run(main())
