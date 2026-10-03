#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

echo "============================================================"
echo "COMPANIES SCHEMA | KOMPLETNÁ DIAGNOSTIKA"
echo "============================================================"

echo
echo "=== 1. VÝSKYTY accepted_material_types ==="
grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules \
  "accepted_material_types" app tests alembic migrations 2>/dev/null || true

echo
echo "=== 2. COMPANY MODEL ==="
grep -RIn --include='*.py' \
  "class Company\|accepted_material_types" app/modules/companies app 2>/dev/null | head -200

echo
echo "=== 3. ALEMBIC MIGRÁCIE ==="
find . -type f \( -name '*.py' -o -name '*.sql' \) \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './node_modules/*' \
  -print0 2>/dev/null |
while IFS= read -r -d '' f; do
  grep -Hn "accepted_material_types" "$f" 2>/dev/null || true
done

echo
echo "=== 4. TEST DB / FIXTURES ==="
grep -RIn --include='*.py' \
  "create_all\|drop_all\|sqlite\|DATABASE_URL\|test.*db\|db_session" \
  tests app 2>/dev/null | head -300

echo
echo "=== 5. SKUTOČNÁ TESTOVACIA SQLITE DB ==="
find . -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './node_modules/*' \
  -print 2>/dev/null

echo
echo "=== 6. SQLITE SCHÉMA companies ==="
while IFS= read -r db; do
  echo "--- $db ---"
  sqlite3 "$db" "PRAGMA table_info(companies);" 2>/dev/null || true
done < <(
  find . -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    -print 2>/dev/null
)

echo
echo "=== 7. PYTEST CONFIG ==="
find . -maxdepth 3 -type f \( \
  -name 'conftest.py' -o \
  -name 'pytest.ini' -o \
  -name 'pyproject.toml' -o \
  -name 'setup.cfg' \
\) -print 2>/dev/null

echo
echo "=== 8. GIT STAV ==="
git status --short
git branch --show-current
git log -1 --oneline

echo
echo "============================================================"
echo "DIAGNOSTIKA HOTOVÁ — NIČ NEBOLO ZMENENÉ"
echo "============================================================"
