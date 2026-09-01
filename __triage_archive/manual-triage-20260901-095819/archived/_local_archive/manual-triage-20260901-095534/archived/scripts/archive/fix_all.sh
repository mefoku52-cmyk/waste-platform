#!/bin/bash

echo "🔧 KOMPLETNÁ OPRAVA - CMEP PLATFORM"
echo "========================================="

# 1. Inštalácia závislostí
echo ""
echo "📋 1. Inštalujem závislosti..."
pip install aiosqlite asyncpg psycopg2-binary

# 2. Nastavenie .env pre PostgreSQL
echo ""
echo "📋 2. Nastavujem .env..."
cat > .env << 'ENVEOF'
DATABASE_URL=postgresql+asyncpg://cmep:cmep@127.0.0.1:5432/cmep
DEBUG=True
APP_NAME=CMEP Platform
ENVEOF

# 3. Vytvorenie tabuliek
echo ""
echo "📋 3. Vytváram tabuľky..."
python3 << 'PYEOF'
import asyncio
import sys
sys.path.insert(0, '.')
from app.shared.infrastructure.db import Base, engine

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Skontroluj vytvorené tabuľky
        result = await conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        tables = [row[0] for row in result.fetchall()]
        print(f'✅ Vytvorené tabuľky: {len(tables)}')
        for t in tables:
            print(f'   - {t}')

asyncio.run(init())
PYEOF

# 4. Spustenie aplikácie
echo ""
echo "📋 4. Spúšťam aplikáciu..."
cd app
uvicorn main:app --reload --port 8001

