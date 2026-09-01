#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROJECT="$HOME/waste-platform"
EMPTY_REVISION="eb259b8c673a"
EMPTY_FILE="$PROJECT/migrations/versions/${EMPTY_REVISION}_popis_zmeny.py"

cd "$PROJECT"

echo "===== BEFORE ====="
alembic current
alembic heads
alembic history --verbose | head -n 80

if [ ! -f "$EMPTY_FILE" ]; then
  echo "ERROR: Expected empty migration was not found:"
  echo "$EMPTY_FILE"
  exit 1
fi

echo
echo "===== VERIFY EMPTY MIGRATION ====="
sed -n '1,220p' "$EMPTY_FILE"

if grep -Eq 'op\.(create_table|drop_table|add_column|drop_column|alter_column|create_index|drop_index|create_foreign_key|drop_constraint)' "$EMPTY_FILE"; then
  echo "ERROR: Migration contains schema operations; refusing deletion."
  exit 1
fi

echo
echo "===== DOWNGRADE ONLY EMPTY REVISION ====="
alembic downgrade -1

echo
echo "===== REMOVE EMPTY REVISION FILE ====="
mkdir -p "$HOME/waste-platform-backups"
cp -av "$EMPTY_FILE" "$HOME/waste-platform-backups/$(basename "$EMPTY_FILE").$(date +%Y%m%d_%H%M%S).bak"
rm -f "$EMPTY_FILE"

find migrations -type d -name '__pycache__' -prune -exec rm -rf {} +

echo
echo "===== AFTER ====="
alembic heads
alembic current
alembic check

echo
echo "===== VERSION FILES ====="
find migrations/versions -maxdepth 1 -type f -name '*.py' -print | sort
