#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

cd "$HOME/waste-platform"

echo "=== BACKUP ==="

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="backups/cmep-typecheck-fix-$STAMP"
mkdir -p "$BACKUP/apps/web/src/app/dashboard/admin"
mkdir -p "$BACKUP/apps/web/src/features/recommendations/components"

cp apps/web/src/app/dashboard/admin/page.tsx \
  "$BACKUP/apps/web/src/app/dashboard/admin/page.tsx"

cp apps/web/src/features/recommendations/components/report-button.tsx \
  "$BACKUP/apps/web/src/features/recommendations/components/report-button.tsx"

echo "Backup: $BACKUP"

echo
echo "=== PATCH TOKEN STORE CALLS ==="

python3 - <<'PY'
from pathlib import Path

paths = [
    Path("apps/web/src/app/dashboard/admin/page.tsx"),
    Path("apps/web/src/features/recommendations/components/report-button.tsx"),
]

old = "tokenStore.getAccessToken?.() || tokenStore.getToken?.()"
new = "tokenStore.getToken()"

for path in paths:
    if not path.exists():
        raise SystemExit("MISSING: " + str(path))

    source = path.read_text(encoding="utf-8")

    if old in source:
        source = source.replace(old, new)
        path.write_text(source, encoding="utf-8")
        print("PATCHED:", path)
    elif new in source:
        print("ALREADY PATCHED:", path)
    else:
        raise SystemExit("EXPECTED TOKEN EXPRESSION NOT FOUND: " + str(path))
PY

echo
echo "=== CONFIRM PATCH ==="

grep -nE "getAccessToken|getToken" \
  apps/web/src/app/dashboard/admin/page.tsx \
  apps/web/src/features/recommendations/components/report-button.tsx \
  || true

echo
echo "=== TYPESCRIPT CHECK ==="

cd apps/web
npm run typecheck

echo
echo "=== GIT DIFF SUMMARY ==="

cd ../..
git diff --stat

echo
echo "=== GIT STATUS ==="
git status --short

echo
echo "DONE"
