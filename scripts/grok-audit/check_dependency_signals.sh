#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${HOME}/waste-platform"
cd "${PROJECT_ROOT}"

echo "=== PRIAME IMPORTY PYDANTIC A BASEMODEL ==="
grep -rnE '(^from pydantic import|^import pydantic|BaseModel|ConfigDict|field_validator|model_validate|class Config:|@validator\()' \
  app --include='*.py' 2>/dev/null || true

echo ""
echo "=== SQLALCHEMY API SIGNÁLY ==="
grep -rnE '(DeclarativeBase|mapped_column|Mapped\[|declarative_base\(|create_async_engine|create_engine)' \
  app --include='*.py' 2>/dev/null || true

echo ""
echo "=== JWT IMPLEMENTÁCIA ==="
grep -rnE '(^import jwt|^from jwt|jose)' \
  app --include='*.py' 2>/dev/null || true

echo ""
echo "=== PASSLIB A HASHOVACÍ BACKEND ==="
grep -rnE '(CryptContext|passlib|bcrypt|argon2)' \
  app --include='*.py' 2>/dev/null || true

echo ""
echo "=== DATABÁZOVÝ DRIVER A URL SCHÉMA ==="
grep -rnE '(asyncpg|psycopg2|psycopg|aiosqlite|sqlite|postgresql)' \
  app --include='*.py' 2>/dev/null || true

if [ -f .env ]; then
  echo ""
  echo "=== DATABASE_URL: IBA SCHÉMA ==="
  grep '^DATABASE_URL=' .env 2>/dev/null \
    | sed -E 's#^DATABASE_URL=([^:]+://).*#DATABASE_URL=\1...#' \
    || true
fi

echo ""
echo "=== UVICORN V DOCKERFILE ==="
grep -n 'uvicorn' app/Dockerfile 2>/dev/null || true

echo ""
echo "=== ALEMBIC / MIGRÁCIE ==="
find . -iname 'alembic.ini' -not -path '*/node_modules/*' -print 2>/dev/null || true
find . -path '*/versions/*.py' -not -path '*/node_modules/*' -print 2>/dev/null || true
