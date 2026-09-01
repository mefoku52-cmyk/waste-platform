#!/data/data/com.termux/files/usr/bin/bash
set -eu

mkdir -p "$HOME/waste-platform-backups"
[ -f var/cmep.db ] && cp -av var/cmep.db "$HOME/waste-platform-backups/cmep.db.$(date +%Y%m%d_%H%M%S).bak" || true
[ -f migrations/versions/001_initial.py ] && cp -av migrations/versions/001_initial.py "$HOME/waste-platform-backups/001_initial.py.$(date +%Y%m%d_%H%M%S).bak" || true

rm -f migrations/versions/001_initial.py
rm -f var/cmep.db

alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
alembic current
alembic check || true

python - <<'PY'
import sqlite3
from pathlib import Path

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

db = Path("var/cmep.db")
print("DB_EXISTS =", db.exists())
if db.exists():
    con = sqlite3.connect(db)
    actual = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    print("MISSING =", sorted(expected - actual))
    print("EXTRA =", sorted(actual - expected))
PY
