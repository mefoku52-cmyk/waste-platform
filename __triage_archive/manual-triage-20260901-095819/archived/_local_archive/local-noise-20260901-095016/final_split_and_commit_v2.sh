#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
STAMP="$(date '+%Y%m%d-%H%M%S')"
LOCAL_ARCHIVE_ROOT="$PROJECT/_local_archive"
LOCAL_ARCHIVE="$LOCAL_ARCHIVE_ROOT/local-noise-$STAMP"
DOWNLOAD_DIR="$HOME/storage/shared/Download"
REPORT_DIR="$PROJECT/reports/repo-hygiene"
REPORT="$REPORT_DIR/final-split-and-commit-$STAMP.txt"

cd "$PROJECT"
mkdir -p "$LOCAL_ARCHIVE" "$DOWNLOAD_DIR" "$REPORT_DIR"

say() {
  printf '\n==> %s\n' "$*"
}

move_if_exists() {
  local path="$1"
  [ -e "$path" ] || return 0

  if [ "$path" = "_local_archive" ] || [ "$path" = "cleanup_archive" ]; then
    mkdir -p "$LOCAL_ARCHIVE_ROOT"
    local target="$LOCAL_ARCHIVE_ROOT/$(basename "$path")-$STAMP"
    mv "$path" "$target"
    echo "MOVED: $path -> $target" >> "$REPORT"
    return 0
  fi

  mkdir -p "$LOCAL_ARCHIVE/$(dirname "$path")"
  mv "$path" "$LOCAL_ARCHIVE/$path"
  echo "MOVED: $path -> $LOCAL_ARCHIVE/$path" >> "$REPORT"
}

: > "$REPORT"
{
  echo "Final split and commit report"
  echo "Generated: $(date -Iseconds)"
  echo "Project: $PROJECT"
  echo
  echo "=== Initial git status ==="
  git status --short || true
} >> "$REPORT"

say "Krok 1: presun lokálneho noise mimo aktívny worktree"
move_if_exists "apps/web/debug.txt"
move_if_exists "apps/web/wifi_scan_20260901_050722.json"
move_if_exists "repo_hygiene_ops_toolbox.sh"
move_if_exists "next_cleanup_split.sh"
move_if_exists "final_split_and_commit.sh"
move_if_exists "final_split_and_commit_v2.sh"
move_if_exists "next"
move_if_exists "output"
move_if_exists "cleanup_archive"
move_if_exists "docker-compose.override.yml.disabled.20260826-203621"

say "Krok 2: backend/docker commit"
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

echo >> "$REPORT"
echo "=== Backend staged diff stat ===" >> "$REPORT"
git diff --cached --stat >> "$REPORT" || true

echo
echo "Backend/docker staged diff:"
git diff --cached --stat
echo
echo "Vytvoriť backend/docker commit? [yes/NO]"
read -r BACKEND_CONFIRM

if [ "$BACKEND_CONFIRM" = "yes" ]; then
  git commit -m "refactor: reconcile backend docker and repository wiring"
  echo "BACKEND COMMIT: done" >> "$REPORT"
else
  echo "BACKEND COMMIT: skipped" >> "$REPORT"
  git restore --staged \
    .dockerignore \
    app/modules/inquiries/infrastructure/repositories.py \
    app/shared/infrastructure/db/session.py \
    docker-compose.yml \
    docker-compose-app-variant.yml \
    docker-compose-original-check.yml \
    docker-compose.monitoring.yml \
    docker-compose.production.yml \
    generate_modules.py || true
fi

say "Krok 3: tracked frontend commit"
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

echo >> "$REPORT"
echo "=== Frontend tracked staged diff stat ===" >> "$REPORT"
git diff --cached --stat >> "$REPORT" || true

echo
echo "Frontend tracked staged diff:"
git diff --cached --stat
echo
echo "Vytvoriť tracked frontend commit? [yes/NO]"
read -r FRONTEND_TRACKED_CONFIRM

if [ "$FRONTEND_TRACKED_CONFIRM" = "yes" ]; then
  git commit -m "refactor(web): consolidate tracked frontend application updates"
  echo "FRONTEND TRACKED COMMIT: done" >> "$REPORT"
else
  echo "FRONTEND TRACKED COMMIT: skipped" >> "$REPORT"
  git restore --staged \
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
    apps/web/src/lib/config.ts || true
fi

say "Krok 4: untracked frontend entrypoints"
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
  apps/web/src/features/uploads/index.ts 2>/dev/null || true

if git diff --cached --quiet; then
  echo "No frontend entrypoint files staged." >> "$REPORT"
else
  echo
  echo "Frontend entrypoint staged diff:"
  git diff --cached --stat
  echo
  echo "Vytvoriť frontend entrypoints commit? [yes/NO]"
  read -r FRONTEND_UNTRACKED_CONFIRM

  if [ "$FRONTEND_UNTRACKED_CONFIRM" = "yes" ]; then
    git commit -m "feat(web): add frontend feature barrel exports and cmep styles"
    echo "FRONTEND UNTRACKED COMMIT: done" >> "$REPORT"
  else
    echo "FRONTEND UNTRACKED COMMIT: skipped" >> "$REPORT"
    git restore --staged \
      apps/web/src/cmep-dark.css \
      apps/web/src/features/admin/index.ts \
      apps/web/src/features/auth/index.ts \
      apps/web/src/features/companies/index.ts \
      apps/web/src/features/compliance/index.ts \
      apps/web/src/features/documents/index.ts \
      apps/web/src/features/inquiries/index.ts \
      apps/web/src/features/listings/index.ts \
      apps/web/src/features/notifications/index.ts \
      apps/web/src/features/uploads/index.ts 2>/dev/null || true
  fi
fi

say "Krok 5: finálny stav"
{
  echo
  echo "=== Final git status ==="
  git status --short || true
  echo
  echo "=== Local archive contents ==="
  find "$LOCAL_ARCHIVE_ROOT" -type f | sort || true
} >> "$REPORT"

cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true

echo
echo "Hotovo."
echo "Report: $REPORT"
echo "Download: $DOWNLOAD_DIR/$(basename "$REPORT")"
echo
git status --short
