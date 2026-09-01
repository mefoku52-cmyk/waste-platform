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
import json

db = sys.argv[1]
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("== DATABASE LIST ==")
for row in cur.execute("PRAGMA database_list").fetchall():
    print(dict(row))
print()

tables = [
    r["name"]
    for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
]

print("== TABLES ==")
for t in tables:
    print("-", t)
print()

print("== TABLE COUNTS ==")
for t in tables:
    n = cur.execute(f'SELECT COUNT(*) AS n FROM "{t}"').fetchone()["n"]
    print(f"{t}: {n}")
print()

for t in tables:
    print(f"== SCHEMA: {t} ==")
    cols = cur.execute(f'PRAGMA table_info("{t}")').fetchall()
    if not cols:
        print("(no columns)")
    else:
        for c in cols:
            print(
                f'{c["cid"]}: {c["name"]} | {c["type"]} | notnull={c["notnull"]} | pk={c["pk"]}'
            )
    print()

    print(f"== SAMPLE ROW: {t} ==")
    try:
        row = cur.execute(f'SELECT * FROM "{t}" LIMIT 1').fetchone()
        if row is None:
            print("(empty)")
        else:
            print(json.dumps({k: row[k] for k in row.keys()}, ensure_ascii=False, default=str, indent=2))
    except Exception as e:
        print(f"ERROR: {e}")
    print()

conn.close()
PY
