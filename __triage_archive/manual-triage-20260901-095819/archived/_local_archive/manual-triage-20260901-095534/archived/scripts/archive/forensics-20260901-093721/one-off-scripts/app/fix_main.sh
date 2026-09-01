#!/bin/bash

echo "🔧 OPRAVA main.py"
echo "========================================="

# 1. Choď do adresára
cd ~/waste-platform/app

# 2. Zálohuj
cp main.py main.py.bak.$(date +%Y%m%d_%H%M%S)

# 3. Vytvor nový main.py
cat > main.py << 'MAINEOF'
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.shared.infrastructure.db.base import Base
from app.shared.infrastructure.db.session import engine
from app.shared.infrastructure.db import register_models  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting up...")
    # create_all je zakomentované - používame Alembic migrácie
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    logging.info("Shutting down...")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/version")
async def version():
    return {"version": "1.0.0", "app": settings.app_name}
MAINEOF

# 4. Skontroluj syntax
echo ""
echo "📋 Kontrola syntaxe..."
python3 -m py_compile main.py && echo "✅ Syntax OK"

# 5. Zabi staré procesy
echo ""
echo "📋 Zastavujem staré procesy..."
pkill -f uvicorn 2>/dev/null
sleep 2

# 6. Spusti aplikáciu
echo ""
echo "📋 Spúšťam aplikáciu..."
uvicorn main:app --reload --port 8000 --host 0.0.0.0 &

# 7. Počkaj a otestuj
sleep 5
echo ""
echo "📋 Test API..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "========================================="
echo "✅ HOTOVO!"
echo "========================================="
