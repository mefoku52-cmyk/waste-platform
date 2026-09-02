#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
STAMP="$(date '+%Y%m%d-%H%M%S')"
TRIAGE_BASE="$PROJECT/__triage_archive"
ARCHIVE_HOME="$HOME/waste-platform-local-archives"
REPORT_DIR="$PROJECT/reports/repo-hygiene"
REPORT="$REPORT_DIR/repo-hygiene-finalize-$STAMP.txt"
DOWNLOAD_DIR="$HOME/storage/shared/Download"

cd "$PROJECT"
mkdir -p "$ARCHIVE_HOME" "$REPORT_DIR" "$DOWNLOAD_DIR" scripts/dev

say() {
  printf '\n==> %s\n' "$*"
}

{
  echo "Repo hygiene finalization"
  echo "Generated: $(date -Iseconds)"
  echo "Project: $PROJECT"
  echo
  echo "=== Status before ==="
  git status --short || true
} > "$REPORT"

say "1. Nájdite posledný triage balík"

LATEST_TRIAGE=""
if [ -d "$TRIAGE_BASE" ]; then
  LATEST_TRIAGE="$(
    find "$TRIAGE_BASE" -mindepth 1 -maxdepth 1 -type d -name 'manual-triage-*' \
      -printf '%T@ %p\n' 2>/dev/null \
      | sort -n \
      | tail -n 1 \
      | cut -d' ' -f2-
  )"
fi

if [ -z "$LATEST_TRIAGE" ] || [ ! -d "$LATEST_TRIAGE" ]; then
  echo "ERROR: Nenašiel som manual-triage-* v $TRIAGE_BASE" | tee -a "$REPORT"
  exit 1
fi

echo "Latest triage: $LATEST_TRIAGE" | tee -a "$REPORT"

say "2. Obnova troch prenositeľných diagnostických helperov"

restore_helper() {
  local name="$1"
  local src="$LATEST_TRIAGE/kept-local/$name"
  local dst="scripts/dev/$name"

  if [ -f "$src" ]; then
    cp -f "$src" "$dst"
    chmod 700 "$dst"
    echo "RESTORED: $src -> $dst" | tee -a "$REPORT"
  else
    echo "MISSING: $src" | tee -a "$REPORT"
  fi
}

restore_helper "check-db-content.sh"
restore_helper "inspect-db-schema.sh"
restore_helper "run-check.sh"

say "3. Presun celého triage archívu mimo Git worktree"

DEST="$ARCHIVE_HOME/$(basename "$LATEST_TRIAGE")"

if [ -e "$DEST" ]; then
  DEST="$ARCHIVE_HOME/$(basename "$LATEST_TRIAGE")-$STAMP"
fi

mv "$LATEST_TRIAGE" "$DEST"
echo "MOVED ARCHIVE: $LATEST_TRIAGE -> $DEST" | tee -a "$REPORT"

if [ -d "$TRIAGE_BASE" ] && [ -z "$(find "$TRIAGE_BASE" -mindepth 1 -print -quit)" ]; then
  rmdir "$TRIAGE_BASE"
  echo "REMOVED EMPTY: $TRIAGE_BASE" | tee -a "$REPORT"
fi

say "4. Gitignore pre lokálny operational odpad"

touch .gitignore

add_ignore() {
  local pattern="$1"
  if ! grep -Fqx "$pattern" .gitignore; then
    printf '\n# Local operational archives and Termux-only helpers\n%s\n' "$pattern" >> .gitignore
    echo "IGNORED: $pattern" | tee -a "$REPORT"
  else
    echo "ALREADY IGNORED: $pattern" | tee -a "$REPORT"
  fi
}

add_ignore "__triage_archive/"
add_ignore "_local_archive/"
add_ignore "reports/repo-hygiene/"
add_ignore "final_untracked_triage*.sh"
add_ignore "audit_remaining_untracked_tools.sh"

say "5. Overenie prenositeľných helperov"

for f in \
  scripts/dev/check-db-content.sh \
  scripts/dev/inspect-db-schema.sh \
  scripts/dev/run-check.sh
do
  echo | tee -a "$REPORT"
  echo "=== $f ===" | tee -a "$REPORT"
  bash -n "$f" 2>&1 | tee -a "$REPORT"
  echo "bash -n exit code: ${PIPESTATUS[0]}" | tee -a "$REPORT"
done

say "6. Git status po vyčistení"

{
  echo
  echo "=== Status after ==="
  git status --short || true
  echo
  echo "=== Suggested staged files ==="
  echo "git add .gitignore scripts/dev/check-db-content.sh scripts/dev/inspect-db-schema.sh scripts/dev/run-check.sh"
  echo
  echo "=== Do not add automatically ==="
  echo "Do not stage app/start_app.sh without making it portable."
  echo "Do not stage archived/review scripts without separate inspection."
  echo
  echo "=== External archive location ==="
  echo "$DEST"
} >> "$REPORT"

cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true

say "Hotovo"
echo "Report: $REPORT"
echo "Download: $DOWNLOAD_DIR/$(basename "$REPORT")"
echo "Archive outside repo: $DEST"
echo
git status --short || true
