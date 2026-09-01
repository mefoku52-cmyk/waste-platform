#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
STAMP="$(date '+%Y%m%d-%H%M%S')"
TRIAGE_BASE="$PROJECT/__triage_archive"
TRIAGE_ROOT="$TRIAGE_BASE/manual-triage-$STAMP"
KEEP_DIR="$TRIAGE_ROOT/kept-local"
ARCHIVE_DIR="$TRIAGE_ROOT/archived"
REVIEW_DIR="$TRIAGE_ROOT/review"
DROP_LIST="$TRIAGE_ROOT/drop-candidates.txt"
REPORT_DIR="$PROJECT/reports/repo-hygiene"
REPORT="$REPORT_DIR/final-untracked-triage-v2-$STAMP.txt"
DOWNLOAD_DIR="$HOME/storage/shared/Download"

cd "$PROJECT"
mkdir -p "$KEEP_DIR" "$ARCHIVE_DIR" "$REVIEW_DIR" "$REPORT_DIR" "$DOWNLOAD_DIR" "$TRIAGE_BASE"

say() {
  printf '\n==> %s\n' "$*"
}

move_to_bucket() {
  local path="$1"
  local bucket="$2"
  [ -e "$path" ] || return 0

  case "$path" in
    "__triage_archive"|".triage_sandbox")
      echo "SKIP self-protected path: $path" >> "$REPORT"
      return 0
      ;;
  esac

  mkdir -p "$bucket/$(dirname "$path")"
  mv "$path" "$bucket/$path"
  echo "MOVED: $path -> $bucket/$path" >> "$REPORT"
}

copy_to_report() {
  local path="$1"
  {
    echo
    echo "----------------------------------------------------------------"
    echo "PATH: $path"
    echo "----------------------------------------------------------------"
    if [ -f "$path" ]; then
      ls -lh "$path"
      echo
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
  echo "Final untracked triage v2"
  echo "Generated: $(date -Iseconds)"
  echo "Project: $PROJECT"
  echo
  echo "=== Initial git status ==="
  git status --short || true
} >> "$REPORT"

say "1. Presun užitočných a archívnych skupín mimo aktívny worktree"

if [ -d "scripts/archive" ]; then
  move_to_bucket "scripts/archive" "$ARCHIVE_DIR"
else
  echo "INFO: scripts/archive already moved or missing" >> "$REPORT"
fi

if [ -d "_local_archive" ]; then
  move_to_bucket "_local_archive" "$ARCHIVE_DIR"
else
  echo "INFO: _local_archive already moved or missing" >> "$REPORT"
fi

say "2. Keep kandidáti"
move_to_bucket "check-db-content.sh" "$KEEP_DIR"
move_to_bucket "inspect-db-schema.sh" "$KEEP_DIR"
move_to_bucket "run-check.sh" "$KEEP_DIR"
move_to_bucket "app/start_app.sh" "$KEEP_DIR"

say "3. Review kandidáti"
move_to_bucket "fix_auth_complete.sh" "$REVIEW_DIR"
move_to_bucket "inspect-cmep-backups.sh" "$REVIEW_DIR"
move_to_bucket "apps/web/rewrite-imports-node.mjs" "$REVIEW_DIR"
move_to_bucket "apps/web/rewrite-imports-sed.sh" "$REVIEW_DIR"
move_to_bucket "apps/web/refactor-cmep.sh" "$REVIEW_DIR"
move_to_bucket "apps/web/refactor-cmep-fix.sh" "$REVIEW_DIR"
move_to_bucket "scripts/fixes/backend" "$REVIEW_DIR"

say "4. Jednorazové web repair skripty do archive"
move_to_bucket "apps/web/fix-imports-and-eslint.sh" "$ARCHIVE_DIR"
move_to_bucket "apps/web/fix-now.sh" "$ARCHIVE_DIR"
move_to_bucket "apps/web/fix_cryptography.sh" "$ARCHIVE_DIR"
move_to_bucket "apps/web/eslint" "$ARCHIVE_DIR"
move_to_bucket "audit_remaining_untracked_tools.sh" "$ARCHIVE_DIR"
move_to_bucket "final_untracked_triage.sh" "$ARCHIVE_DIR"
move_to_bucket "final_untracked_triage_v2.sh" "$ARCHIVE_DIR"

say "5. Drop kandidátov len evidujem"
for p in \
  "apps/web/eslint" \
  "apps/web/fix-now.sh" \
  "apps/web/fix_cryptography.sh"
do
  echo "$p" >> "$DROP_LIST"
done

say "6. Report summary"
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

say "7. Sample contents"
copy_to_report "$KEEP_DIR/check-db-content.sh"
copy_to_report "$KEEP_DIR/inspect-db-schema.sh"
copy_to_report "$KEEP_DIR/run-check.sh"
copy_to_report "$KEEP_DIR/app/start_app.sh"
copy_to_report "$REVIEW_DIR/fix_auth_complete.sh"
copy_to_report "$REVIEW_DIR/inspect-cmep-backups.sh"
copy_to_report "$REVIEW_DIR/apps/web/rewrite-imports-node.mjs"
copy_to_report "$REVIEW_DIR/apps/web/rewrite-imports-sed.sh"
copy_to_report "$REVIEW_DIR/apps/web/refactor-cmep.sh"
copy_to_report "$REVIEW_DIR/apps/web/refactor-cmep-fix.sh"
copy_to_report "$REVIEW_DIR/scripts/fixes/backend"

say "8. Suggested next git add"
cat >> "$REPORT" <<'NEXT'
=== Suggested next git add ===
Ak budeš chcieť spraviť malý helper commit, najpravdepodobnejší shortlist je:

git add \
  check-db-content.sh \
  inspect-db-schema.sh \
  run-check.sh

app/start_app.sh je skôr lokálny convenience wrapper.
Review a archived položky teraz necommitovať bez ďalšieho čítania.
NEXT

cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true

say "Hotovo"
echo "Report: $REPORT"
echo "Download: $DOWNLOAD_DIR/$(basename "$REPORT")"
echo
echo "Aktuálny git status:"
git status --short || true
