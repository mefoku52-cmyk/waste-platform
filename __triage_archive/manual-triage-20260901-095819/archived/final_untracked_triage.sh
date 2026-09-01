#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
STAMP="$(date '+%Y%m%d-%H%M%S')"
TRIAGE_ROOT="$PROJECT/_local_archive/manual-triage-$STAMP"
KEEP_DIR="$TRIAGE_ROOT/kept-local"
ARCHIVE_DIR="$TRIAGE_ROOT/archived"
REVIEW_DIR="$TRIAGE_ROOT/review"
DROP_LIST="$TRIAGE_ROOT/drop-candidates.txt"
REPORT_DIR="$PROJECT/reports/repo-hygiene"
REPORT="$REPORT_DIR/final-untracked-triage-$STAMP.txt"
DOWNLOAD_DIR="$HOME/storage/shared/Download"

cd "$PROJECT"
mkdir -p "$KEEP_DIR" "$ARCHIVE_DIR" "$REVIEW_DIR" "$REPORT_DIR" "$DOWNLOAD_DIR"

say() {
  printf '\n==> %s\n' "$*"
}

move_to_bucket() {
  local path="$1"
  local bucket="$2"
  [ -e "$path" ] || return 0
  mkdir -p "$bucket/$(dirname "$path")"
  mv "$path" "$bucket/$path"
  echo "MOVED: $path -> $bucket/$path" >> "$REPORT"
}

copy_to_report() {
  local path="$1"
  {
    echo
    echo "--- $path ---"
    if [ -f "$path" ]; then
      ls -lh "$path"
      sed -n '1,60p' "$path" 2>/dev/null || true
    elif [ -d "$path" ]; then
      echo "[directory]"
      find "$path" -maxdepth 3 \( -type f -o -type d \) | sort | sed -n '1,120p'
    else
      echo "[missing]"
    fi
  } >> "$REPORT"
}

: > "$REPORT"
: > "$DROP_LIST"

{
  echo "Final untracked triage"
  echo "Generated: $(date -Iseconds)"
  echo "Project: $PROJECT"
  echo
  echo "=== Initial git status ==="
  git status --short || true
} >> "$REPORT"

say "1. Jednoznačné archívy nechávam mimo aktívneho worktree"
move_to_bucket "scripts/archive" "$ARCHIVE_DIR"
move_to_bucket "_local_archive" "$ARCHIVE_DIR"

say "2. Root a web helpery rozdeľujem"
move_to_bucket "app/start_app.sh" "$KEEP_DIR"
move_to_bucket "check-db-content.sh" "$KEEP_DIR"
move_to_bucket "inspect-db-schema.sh" "$KEEP_DIR"
move_to_bucket "run-check.sh" "$KEEP_DIR"

move_to_bucket "fix_auth_complete.sh" "$REVIEW_DIR"
move_to_bucket "inspect-cmep-backups.sh" "$REVIEW_DIR"

move_to_bucket "apps/web/rewrite-imports-node.mjs" "$REVIEW_DIR"
move_to_bucket "apps/web/rewrite-imports-sed.sh" "$REVIEW_DIR"
move_to_bucket "apps/web/refactor-cmep.sh" "$REVIEW_DIR"
move_to_bucket "apps/web/refactor-cmep-fix.sh" "$REVIEW_DIR"

move_to_bucket "apps/web/fix-imports-and-eslint.sh" "$ARCHIVE_DIR"
move_to_bucket "apps/web/fix-now.sh" "$ARCHIVE_DIR"
move_to_bucket "apps/web/fix_cryptography.sh" "$ARCHIVE_DIR"
move_to_bucket "apps/web/eslint" "$ARCHIVE_DIR"

move_to_bucket "audit_remaining_untracked_tools.sh" "$ARCHIVE_DIR"

say "3. Backend fixes tree nechávam na review"
move_to_bucket "scripts/fixes/backend" "$REVIEW_DIR"

say "4. Drop kandidátov len zapisujem, nemažem"
for p in \
  "apps/web/eslint" \
  "apps/web/fix-now.sh" \
  "apps/web/fix_cryptography.sh"
do
  echo "$p" >> "$DROP_LIST"
done

say "5. Snapshot reportu"
{
  echo
  echo "=== KEEP LOCAL ==="
  find "$KEEP_DIR" -type f | sort || true
  echo
  echo "=== ARCHIVED ==="
  find "$ARCHIVE_DIR" -type f | sort || true
  echo
  echo "=== REVIEW ==="
  find "$REVIEW_DIR" -type f | sort || true
  echo
  echo "=== DROP CANDIDATES ==="
  cat "$DROP_LIST"
} >> "$REPORT"

say "6. Obsah KEEP a REVIEW vzoriek"
copy_to_report "$KEEP_DIR/app/start_app.sh"
copy_to_report "$KEEP_DIR/check-db-content.sh"
copy_to_report "$KEEP_DIR/inspect-db-schema.sh"
copy_to_report "$KEEP_DIR/run-check.sh"
copy_to_report "$REVIEW_DIR/fix_auth_complete.sh"
copy_to_report "$REVIEW_DIR/inspect-cmep-backups.sh"
copy_to_report "$REVIEW_DIR/apps/web/rewrite-imports-node.mjs"
copy_to_report "$REVIEW_DIR/apps/web/rewrite-imports-sed.sh"
copy_to_report "$REVIEW_DIR/apps/web/refactor-cmep.sh"
copy_to_report "$REVIEW_DIR/apps/web/refactor-cmep-fix.sh"
copy_to_report "$REVIEW_DIR/scripts/fixes/backend"

say "7. Návrh ďalšieho git add"
cat >> "$REPORT" <<'NEXT'
=== Suggested next git add ===
Ak chceš commitnúť len rozumné helpery, najprv ich vráť z kept-local do repa alebo ich presuň do scripts/ops či scripts/dev, potom použi niečo ako:

git add \
  check-db-content.sh \
  inspect-db-schema.sh \
  run-check.sh

app/start_app.sh skôr zváž ako lokálny convenience skript, nie povinný repo commit.

Všetko v archived a väčšinu review teraz necommitovať.
NEXT

cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true

say "Hotovo"
echo "Report: $REPORT"
echo "Download: $DOWNLOAD_DIR/$(basename "$REPORT")"
echo
echo "Aktuálny git status:"
git status --short || true
