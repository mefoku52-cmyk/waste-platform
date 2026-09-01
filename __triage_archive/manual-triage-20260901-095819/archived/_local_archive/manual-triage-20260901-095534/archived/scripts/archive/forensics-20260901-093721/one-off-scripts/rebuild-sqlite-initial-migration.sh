#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROJECT="$HOME/waste-platform"
cd "$PROJECT"

echo "===== 1. LIST MIGRATION FILES ====="
find migrations -maxdepth 3 -type f | sort

echo
echo "===== 2. BACKUP CURRENT DB + MIGRATIONS ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$HOME/waste-platform-backups"

[ -f var/cmep.db ] && cp -av var/cmep.db "$HOME/waste-platform-backups/cmep.db.$STAMP.bak" || true
[ -d migrations/versions ] && cp -av migrations/versions "$HOME/waste-platform-backups/versions.$STAMP.bak" || true

echo
echo "===== 3. REMOVE OLD SQLITE FILE ====="
rm -f var/cmep.db
mkdir -p var

echo
echo "===== 4. SHOW OLD VERSION FILE CONTENT ====="
if [ -f migrations/versions/001_initial.py ]; then
  sed -n '1,220p' migrations/versions/001_initial.py
else
  echo "001_initial.py NOT FOUND"
fi

echo
echo "===== 5. REMOVE OLD VERSION FILES ====="
find migrations/versions -maxdepth 1 -type f -name '*.py' ! -name '__init__.py' -print -delete || true
find migrations/versions -maxdepth 1 -type f -name '*.pyc' -print -delete || true

echo
echo "===== 6. VERIFY MODEL IMPORT + TABLE COUNT ====="
python - <<'PY'
import app.shared.infrastructure.db.register_models  # noqa: F401
from app.shared.infrastructure.db.base import Base

tables = sorted(Base.metadata.tables.keys())
print("TABLE_COUNT =", len(tables))
for name in tables:
    print(name)
PY

echo
echo "===== 7. AUTOGENERATE INITIAL MIGRATION ====="
alembic revision --autogenerate -m "initial_schema"

echo
echo "===== 8. SHOW GENERATED MIGRATION ====="
LATEST="$(find migrations/versions -maxdepth 1 -type f -name '*.py' ! -name '__init__.py' | sort | tail -n 1)"
echo "LATEST=$LATEST"
sed -n '1,260p' "$LATEST"

echo
echo "===== 9. APPLY MIGRATION ====="
alembic upgrade head

echo
echo "===== 10. SHOW ALEMBIC STATE ====="
alembic heads || true
alembic current || true

echo
echo "===== 11. SQLITE TABLE INVENTORY ====="
python - <<'PY'
import sqlite3
from pathlib import Path

db = Path("var/cmep.db")
print("DB_PATH =", db.resolve())
print("DB_EXISTS =", db.exists())

if db.exists():
    con = sqlite3.connect(db)
    rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for row in rows:
        print(row[0])
    con.close()
PY

echo
echo "===== 12. CHECK EXPECTED TABLES ====="
python - <<'PY'
import sqlite3

expected = {
    "admin_audit_entries",
    "analytics_events",
    "companies",
    "company_memberships",
    "compliance_records",
    "documents",
    "inquiries",
    "listings",
    "notifications",
    "refresh_sessions",
    "users",
    "alembic_version",
}

con = sqlite3.connect("var/cmep.db")
actual = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
con.close()

print("MISSING =", sorted(expected - actual))
print("EXTRA =", sorted(actual - expected))
print("ALL_OK =", expected.issubset(actual))
PY

echo
echo "===== 13. ALEMBIC CHECK ====="
alembic check || true
