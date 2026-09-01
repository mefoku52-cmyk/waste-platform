#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

CANDIDATES=(
  "$HOME/waste-platform/var/cmep.db"
  "$HOME/waste-platform/var/wasteplatform.db"
  "$HOME/waste-platform/waste.db"
  "$HOME/waste-platform/backups/cmep.db.20260825071451.bak"
  "$HOME/waste-platform/backups/cmep.db.20260825071700.bak"
  "$HOME/waste-platform/cleanup/archive/databases/cmep.db"
  "$HOME/waste-platform/cleanup/archive/databases/wasteplatformtest2.db"
)

for db in "${CANDIDATES[@]}"; do
  echo "============================================================"
  echo "FILE: $db"

  if [ ! -f "$db" ]; then
    echo "MISSING"
    echo
    continue
  fi

  ls -lh "$db"
  file "$db" || true

  python - <<'PY' "$db"
import sqlite3
import sys

db = sys.argv[1]
wanted = [
    "users",
    "companies",
    "company_memberships",
    "listings",
    "documents",
    "inquiries",
    "notifications",
    "compliance_records",
]

try:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    tables = {
        row["name"]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }

    print("TABLES:", ", ".join(sorted(tables)) if tables else "(none)")
    print("COUNTS:")

    for table in wanted:
        if table in tables:
            count = cur.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"]
            print(f"  {table}: {count}")
        else:
            print(f"  {table}: MISSING")

    if "companies" in tables:
        rows = cur.execute(
            "SELECT id, legal_name, status, city FROM companies ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        print("COMPANY SAMPLE:")
        for row in rows:
            print(" ", dict(row))

    if "listings" in tables:
        rows = cur.execute(
            "SELECT id, title, material_type, quantity, unit, status FROM listings ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        print("LISTING SAMPLE:")
        for row in rows:
            print(" ", dict(row))

    conn.close()

except Exception as e:
    print("NOT A READABLE SQLITE DATABASE:", e)
PY

  echo
done
