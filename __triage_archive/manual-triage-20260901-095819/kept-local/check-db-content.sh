#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

DB="${1:-./var/cmep.db}"

echo "== DB FILE =="
echo "$DB"
echo

if [ ! -f "$DB" ]; then
  echo "ERROR: databaza neexistuje: $DB"
  exit 1
fi

python - <<'PY' "$DB"
import sqlite3
import sys

db = sys.argv[1]
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("== TABLES ==")
tables = [
    r["name"]
    for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
]
for t in tables:
    print("-", t)
print()

print("== ROW COUNTS ==")
for t in tables:
    try:
        n = cur.execute(f'SELECT COUNT(*) AS n FROM "{t}"').fetchone()["n"]
        print(f"{t}: {n}")
    except Exception as e:
        print(f"{t}: ERROR: {e}")
print()

def show_query(title, query):
    print(f"== {title} ==")
    try:
        rows = cur.execute(query).fetchall()
        if not rows:
            print("(empty)")
        else:
            cols = rows[0].keys()
            print(" | ".join(cols))
            print("-" * 80)
            for row in rows:
                print(" | ".join("" if row[c] is None else str(row[c]) for c in cols))
    except Exception as e:
        print(f"ERROR: {e}")
    print()

show_query(
    "USERS",
    """
    SELECT id, email, status, firstName, lastName, displayName
    FROM users
    ORDER BY email
    LIMIT 20
    """
)

show_query(
    "COMPANIES",
    """
    SELECT id, legalName, tradingName, status, countryCode, city
    FROM companies
    ORDER BY legalName
    LIMIT 20
    """
)

show_query(
    "LISTINGS",
    """
    SELECT id, title, materialType, quantity, unit, status, companyId
    FROM listings
    ORDER BY title
    LIMIT 20
    """
)

show_query(
    "INQUIRIES",
    """
    SELECT id, listingId, companyId, status, contactEmail
    FROM inquiries
    ORDER BY id
    LIMIT 20
    """
)

show_query(
    "DOCUMENTS",
    """
    SELECT id, title, documentType, status, companyId
    FROM documents
    ORDER BY title
    LIMIT 20
    """
)

show_query(
    "NOTIFICATIONS",
    """
    SELECT id, userId, type, title, isRead
    FROM notifications
    ORDER BY id
    LIMIT 20
    """
)

show_query(
    "COMPANY MEMBERSHIPS",
    """
    SELECT id, companyId, userId, membershipRole, status, isPrimaryContact
    FROM companymemberships
    ORDER BY id
    LIMIT 20
    """
)

conn.close()
PY
