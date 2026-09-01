#!/usr/bin/env python3
import os, re, shutil
from pathlib import Path

BASE = Path("/data/data/com.termux/files/home/waste-platform")
os.chdir(BASE)

print("=== [1/5] Opravujem Settings (database fallback) ===")
config_candidates = [BASE / "app/core/config.py", BASE / "app/shared/config.py", BASE / "app/config.py"]
config_file = next((c for c in config_candidates if c.exists()), None)

if config_file:
    print(f"  Nájdený: {config_file}")
    content = config_file.read_text()
    if "Settings.database" in content or "hasattr(Settings, 'database')" in content:
        print("  Už opravené, preskakujem")
    else:
        shutil.copy(config_file, str(config_file) + ".bak")
        fallback = '''
# --- AUTO-FIX: database fallback ---
import os
class _DatabaseFallback:
    async_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    sync_url = os.getenv("DATABASE_SYNC_URL", "sqlite:///./app.db")
    echo = False

def _database_property(self):
    return _DatabaseFallback()

Settings.database = property(_database_property)
# --- END AUTO-FIX ---
'''
        config_file.write_text(content + fallback)
        print("  [OK] Settings opravené")
else:
    print("  [WARN] config.py nenájdený")

print("\n=== [2/5] Opravujem session.py ===")
session_file = BASE / "app/shared/infrastructure/db/session.py"
if session_file.exists():
    shutil.copy(session_file, str(session_file) + ".bak")
    session_file.write_text('''import os
try:
    from app.core.config import settings
    _db_url = os.getenv("DATABASE_URL")
    if not _db_url:
        _db_url = getattr(settings, 'database', None) and settings.database.async_url or "sqlite+aiosqlite:///./app.db"
    DATABASE_URL = _db_url
except Exception:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_async_engine(DATABASE_URL, echo=False, poolclass=StaticPool, connect_args=connect_args)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session_maker() as session:
        yield session

get_db_session = get_db
''')
    print("  [OK] session.py opravený")

print("\n=== [3/5] Vytváram chýbajúce modely ===")
for mod in ["inquiries", "documents", "compliance", "notifications", "analytics", "admin"]:
    mod_dir = BASE / "app/modules" / mod
    mod_dir.mkdir(parents=True, exist_ok=True)
    init_file = mod_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    model_file = mod_dir / "models.py"
    if not model_file.exists():
        mod_cap = mod.capitalize()
        model_file.write_text(f'''from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.shared.infrastructure.db.base import Base

class {mod_cap}Record(Base):
    __tablename__ = "{mod}"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
''')
        print(f"  [+] {model_file}")

print("\n=== [4/5] Opravujem frontend API URL ===")
web_src = BASE / "apps/web/src"
fixed = []
if web_src.exists():
    for f in web_src.rglob("*.ts*"):
        try:
            content = f.read_text()
            if "/api/v1/api/v1" in content:
                shutil.copy(f, str(f) + ".bak")
                f.write_text(content.replace("/api/v1/api/v1", "/api/v1"))
                fixed.append(str(f))
        except Exception:
            pass
for env_name in [".env", "apps/web/.env.local", "apps/web/.env"]:
    env_path = BASE / env_name
    if env_path.exists():
        content = env_path.read_text()
        if "/api/v1/api/v1" in content:
            shutil.copy(env_path, str(env_path) + ".bak")
            env_path.write_text(content.replace("/api/v1/api/v1", "/api/v1"))
            fixed.append(str(env_name))
if fixed:
    for f in fixed:
        print(f"  [FIX] {f}")
else:
    print("  Nič na opravu")

print("\n=== [5/5] Kontrola .env a reštart ===")
env_file = BASE / ".env"
env_text = env_file.read_text() if env_file.exists() else ""
if "DATABASE_URL=" not in env_text:
    with open(env_file, "a") as f:
        f.write("\nDATABASE_URL=sqlite+aiosqlite:///./app.db\n")
    print("  [+] DATABASE_URL pridané do .env")

print("\nZabíjam staré procesy...")
os.system("pkill -f uvicorn 2>/dev/null; pkill -f 'next dev' 2>/dev/null; sleep 2")

print("Spúšťam aplikáciu...\n")
os.execvp("bash", ["bash", "./start_app.sh"])
