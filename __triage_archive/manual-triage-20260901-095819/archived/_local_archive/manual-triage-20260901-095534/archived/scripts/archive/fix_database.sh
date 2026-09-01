#!/bin/bash

echo "🔧 KOMPLETNÁ OPRAVA DATABÁZY"
echo "========================================="

# 1. Vytvor base.py
echo ""
echo "📋 1. Vytváram base.py..."
mkdir -p app/shared/infrastructure/db
cat > app/shared/infrastructure/db/base.py << 'BASE_EOF'
from sqlalchemy.orm import declarative_base
Base = declarative_base()
BASE_EOF

# 2. Vytvor session.py
echo ""
echo "📋 2. Vytváram session.py..."
cat > app/shared/infrastructure/db/session.py << 'SESSION_EOF'
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cmep.db")
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
SESSION_EOF

# 3. Vytvor __init__.py
echo ""
echo "📋 3. Vytváram __init__.py..."
cat > app/shared/infrastructure/db/__init__.py << 'INIT_EOF'
from app.shared.infrastructure.db.base import Base
from app.shared.infrastructure.db.session import engine, async_session_maker, get_db
__all__ = ["Base", "engine", "async_session_maker", "get_db"]
INIT_EOF

# 4. Vytvor .env
echo ""
echo "📋 4. Vytváram .env..."
cat > .env << 'ENV_EOF'
DATABASE_URL=sqlite+aiosqlite:///./cmep.db
DEBUG=True
APP_NAME=CMEP Platform
ENV_EOF

# 5. Vytvor tabuľky
echo ""
echo "📋 5. Vytváram tabuľky..."
python3 << 'PY_EOF'
import asyncio
import sys
sys.path.insert(0, '.')
from app.shared.infrastructure.db import Base, engine

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Tabuľky vytvorené!')

asyncio.run(init())
PY_EOF

# 6. Spusti aplikáciu
echo ""
echo "📋 6. Spúšťam aplikáciu..."
cd app && uvicorn main:app --reload --port 8000

