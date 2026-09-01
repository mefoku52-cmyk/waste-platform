#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
STAMP="$(date '+%Y%m%d-%H%M%S')"
REPORT_DIR="$PROJECT/reports/repo-hygiene"
REPORT="$REPORT_DIR/next-cleanup-split-$STAMP.txt"
DOWNLOAD_DIR="$HOME/storage/shared/Download"

cd "$PROJECT"

mkdir -p "$REPORT_DIR" "$DOWNLOAD_DIR"

say() {
  printf '\n==> %s\n' "$*"
}

append_section() {
  {
    echo
    echo "### $1 ###"
    shift
    "$@" || true
  } >> "$REPORT"
}

: > "$REPORT"
{
  echo "Next cleanup split report"
  echo "Generated: $(date -Iseconds)"
  echo "Project: $PROJECT"
} >> "$REPORT"

say "Aktuálny git status"
git status --short | tee -a "$REPORT"

say "Skupina A: tracked backend/docker changes"
append_section "tracked-backend-docker" bash -lc "
git status --short | grep -E '^( M|M | D|D ) (\\.dockerignore|app/modules/inquiries/infrastructure/repositories.py|app/shared/infrastructure/db/session.py|docker-compose.yml|docker-compose-app-variant.yml|docker-compose-original-check.yml|docker-compose.monitoring.yml|docker-compose.production.yml|generate_modules.py)$'
"

say "Skupina B: tracked frontend changes"
append_section "tracked-frontend" bash -lc "
git status --short | grep -E '^( M|M ) (apps/web/eslint.config.mjs|apps/web/package-lock.json|apps/web/package.json|apps/web/src/app/|apps/web/src/components/providers/app-providers.tsx|apps/web/src/features/auth/components/login-form.tsx|apps/web/src/features/auth/hooks/use-auth-required.ts|apps/web/src/features/listings/components/listing-form.tsx|apps/web/src/lib/api/http.ts|apps/web/src/lib/auth/token-store.ts|apps/web/src/lib/config.ts)'
"

say "Skupina C: untracked frontend candidates"
append_section "untracked-frontend-candidates" bash -lc "
git ls-files --others --exclude-standard | grep -E '^(apps/web/(fix-imports-and-eslint\\.sh|fix-now\\.sh|fix_cryptography\\.sh|refactor-cmep-fix\\.sh|refactor-cmep\\.sh|rewrite-imports-node\\.mjs|rewrite-imports-sed\\.sh|src/cmep-dark\\.css|src/features/.+/index\\.ts|debug\\.txt|wifi_scan_.*\\.json)|next)$'
"

say "Skupina D: local noise / outputs / archives"
append_section "local-noise" bash -lc "
git ls-files --others --exclude-standard | grep -E '^(cleanup_archive/|output/|repo_hygiene_ops_toolbox\\.sh|docker-compose\\.override\\.yml\\.disabled\\.|apps/web/debug\\.txt|apps/web/wifi_scan_.*\\.json)$'
"

say "Skupina E: misc untracked root scripts"
append_section "misc-untracked-scripts" bash -lc "
git ls-files --others --exclude-standard | grep -E '^(app/start_app\\.sh|check-db-content\\.sh|fix_auth_complete\\.sh|inspect-cmep-backups\\.sh|inspect-db-schema\\.sh|run-check\\.sh|scripts/fixes/backend/.*)$'
"

say "Odporúčané git add bloky"
cat >> "$REPORT" <<'BLOCKS'

### suggested-backend-commit ###
git add \
  .dockerignore \
  app/modules/inquiries/infrastructure/repositories.py \
  app/shared/infrastructure/db/session.py \
  docker-compose.yml
git add -u \
  docker-compose-app-variant.yml \
  docker-compose-original-check.yml \
  docker-compose.monitoring.yml \
  docker-compose.production.yml \
  generate_modules.py

### suggested-frontend-tracked-commit ###
git add \
  apps/web/eslint.config.mjs \
  apps/web/package-lock.json \
  apps/web/package.json \
  apps/web/src/app/dashboard/admin/page.tsx \
  apps/web/src/app/dashboard/companies/new/page.tsx \
  apps/web/src/app/dashboard/documents/new/page.tsx \
  apps/web/src/app/dashboard/listings/[id]/page.tsx \
  apps/web/src/app/dashboard/listings/new/page.tsx \
  apps/web/src/app/dashboard/page.tsx \
  apps/web/src/app/forgot-password/page.tsx \
  apps/web/src/app/globals.css \
  apps/web/src/app/layout.tsx \
  apps/web/src/app/login/page.tsx \
  apps/web/src/app/register/page.tsx \
  apps/web/src/app/reset-password/page.tsx \
  apps/web/src/components/providers/app-providers.tsx \
  apps/web/src/features/auth/components/login-form.tsx \
  apps/web/src/features/auth/hooks/use-auth-required.ts \
  apps/web/src/features/listings/components/listing-form.tsx \
  apps/web/src/lib/api/http.ts \
  apps/web/src/lib/auth/token-store.ts \
  apps/web/src/lib/config.ts

### suggested-frontend-untracked-review ###
git add \
  apps/web/src/cmep-dark.css \
  apps/web/src/features/admin/index.ts \
  apps/web/src/features/auth/index.ts \
  apps/web/src/features/companies/index.ts \
  apps/web/src/features/compliance/index.ts \
  apps/web/src/features/documents/index.ts \
  apps/web/src/features/inquiries/index.ts \
  apps/web/src/features/listings/index.ts \
  apps/web/src/features/notifications/index.ts \
  apps/web/src/features/uploads/index.ts

### suggested-ignore-or-archive ###
cleanup_archive/
output/
apps/web/debug.txt
apps/web/wifi_scan_*.json
repo_hygiene_ops_toolbox.sh
next
docker-compose.override.yml.disabled.20260826-203621
BLOCKS

say "Kópia reportu do Download"
cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true

say "Hotovo"
echo "Report: $REPORT"
echo "Download copy: $DOWNLOAD_DIR/$(basename "$REPORT")"
echo
echo "Teraz si pozri:"
echo "sed -n '1,260p' \"$REPORT\""
