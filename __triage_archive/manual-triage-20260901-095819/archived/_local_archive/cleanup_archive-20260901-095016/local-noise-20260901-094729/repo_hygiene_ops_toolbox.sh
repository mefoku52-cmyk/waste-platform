#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
STAMP="$(date '+%Y%m%d-%H%M%S')"
REPORT_DIR="$PROJECT/reports/repo-hygiene"
REPORT="$REPORT_DIR/repo-hygiene-$STAMP.txt"
ARCHIVE_ROOT="$PROJECT/scripts/archive"
ARCHIVE_DIR="$ARCHIVE_ROOT/forensics-$STAMP"
DOWNLOAD_DIR="$HOME/storage/shared/Download"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

note() {
  printf '\n==> %s\n' "$*"
}

require_file() {
  [ -f "$1" ] || die "Chýba požadovaný súbor: $1"
}

cd "$PROJECT" 2>/dev/null || die "Projekt neexistuje: $PROJECT"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Nie si v Git repozitári."

mkdir -p "$REPORT_DIR" "$ARCHIVE_ROOT" "$DOWNLOAD_DIR"

note "Základný stav repozitára"
{
  echo "Waste Platform repository hygiene report"
  echo "Generated: $(date -Iseconds)"
  echo "Project: $PROJECT"
  echo
  echo "=== Git branch ==="
  git branch --show-current || true
  echo
  echo "=== HEAD ==="
  git log -1 --oneline || true
  echo
  echo "=== Status before actions ==="
  git status --short || true
  echo
  echo "=== Recent commits ==="
  git log --oneline -12 || true
  echo
  echo "=== Tracked diff stat ==="
  git diff --stat || true
  echo
  echo "=== Staged diff stat ==="
  git diff --cached --stat || true
} | tee "$REPORT"

note "Kontrola zvyšných untracked súborov"
mapfile -t UNTRACKED < <(git ls-files --others --exclude-standard)

{
  echo
  echo "=== Untracked files before actions ==="
  if [ "${#UNTRACKED[@]}" -eq 0 ]; then
    echo "(none)"
  else
    printf '%s\n' "${UNTRACKED[@]}"
  fi
} | tee -a "$REPORT"

FORENSIC_FILES=(
  "CMEP-refresh-rotation-forensic-20260824-191333.txt"
  "alembic.ini.backup.20260824-092956"
  "apps/web/chyby.err"
  "dependency-forensic-report.json"
  "scripts/forensic-audit-report-20260824-022021.txt"
  "waste_platform_diagnosis_20260825-134220.txt"
  "yshwss.zip"
)

ONE_OFF_SCRIPTS=(
  "app/fix_and_start.sh"
  "app/fix_app.sh"
  "app/fix_main.sh"
  "apps/web/fix_everything.sh"
  "audit-frontend-runtime-3001.sh"
  "crypto_abi_diagnose.sh"
  "crypto_deep_diag.sh"
  "dependency_forensic_audit.py"
  "dependency_forensic_deep.py"
  "dependency_import_repair_plan.py"
  "dependency_import_runtime_audit.py"
  "diagnose_waste_platform.sh"
  "fix-and-start-frontend-3001.sh"
  "fix-auth-exception-mapping-safe.sh"
  "fix-auth-exception-mapping.sh"
  "fix-main-py-handler-placement-no-python.sh"
  "fix-main-py-handler-placement.sh"
  "fix-next-tracing-termux.sh"
  "fix-sqlite-uuid-alembic-check.sh"
  "fix_all.py"
  "move_audit_to_phone.sh"
  "rebuild-sqlite-initial-migration.sh"
  "remove-empty-alembic-revision.sh"
  "repair-main-py-completely.sh"
  "reset-initial-migration-sqlite.sh"
  "step1_remove_backups.sh"
  "step2_remove_duplicate_models.sh"
  "step3_archive_temp_scripts.sh"
  "step4_clean_env_variants.sh"
  "step5_fix_frontend_auth.sh"
  "test-next-prod-vs-dev.sh"
  "waste_platform_python_audit.sh"
)

KEEP_OPS_FILES=(
  "check-live-auth-status.sh"
  "check-postgres-reachability.sh"
  "classify_git_env_secrets.sh"
  "create-recyclehub-db.sh"
  "init-postgres-termux.sh"
  "seed_database.py"
  "start-postgres-safe.sh"
  "verify-db-and-login.sh"
)

note "Klasifikácia"
{
  echo
  echo "=== Intended long-term dev/ops utilities ==="
  for path in "${KEEP_OPS_FILES[@]}"; do
    [ -e "$path" ] && echo "KEEP: $path"
  done

  echo
  echo "=== Forensic/report artifacts proposed for archive ==="
  for path in "${FORENSIC_FILES[@]}"; do
    [ -e "$path" ] && echo "ARCHIVE: $path"
  done

  echo
  echo "=== One-off repair scripts proposed for archive ==="
  for path in "${ONE_OFF_SCRIPTS[@]}"; do
    [ -e "$path" ] && echo "ARCHIVE: $path"
  done

  echo
  echo "=== Existing archive/fix directories ==="
  [ -d "scripts/archive" ] && find scripts/archive -maxdepth 2 -type f | sort || true
  [ -d "scripts/fixes/backend" ] && find scripts/fixes/backend -maxdepth 2 -type f | sort || true
} | tee -a "$REPORT"

note "Overenie bez zásahu"
echo "Report uložený: $REPORT"
echo
echo "Tento skript zatiaľ NIC nemaže ani nepresúva."
echo "Pokračovať s archiváciou jednorazových súborov? [yes/NO]"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Archivácia zrušená. Audit ostal uložený v: $REPORT"
  cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true
  exit 0
fi

note "Archivácia jednorazových artefaktov"
mkdir -p "$ARCHIVE_DIR/forensics" "$ARCHIVE_DIR/one-off-scripts"

move_to_archive() {
  local source="$1"
  local bucket="$2"
  local target="$ARCHIVE_DIR/$bucket/$source"

  [ -e "$source" ] || return 0
  mkdir -p "$(dirname "$target")"
  mv "$source" "$target"
  echo "MOVED: $source -> $target" | tee -a "$REPORT"
}

for path in "${FORENSIC_FILES[@]}"; do
  move_to_archive "$path" "forensics"
done

for path in "${ONE_OFF_SCRIPTS[@]}"; do
  move_to_archive "$path" "one-off-scripts"
done

note "Príprava stabilných ops skriptov"
mkdir -p scripts/ops

for path in "${KEEP_OPS_FILES[@]}"; do
  [ -e "$path" ] || continue

  base="$(basename "$path")"
  target="scripts/ops/$base"

  if [ "$path" != "$target" ]; then
    mv "$path" "$target"
    echo "MOVED: $path -> $target" | tee -a "$REPORT"
  fi

  if [[ "$target" == *.sh ]]; then
    chmod 700 "$target"
  fi
done

note "Doplnenie bezpečných ignore pravidiel"
IGNORE_MARKER_BEGIN="# --- local forensic and generated artifact ignores ---"
IGNORE_MARKER_END="# --- end local forensic and generated artifact ignores ---"

if ! grep -Fq "$IGNORE_MARKER_BEGIN" .gitignore 2>/dev/null; then
  cat >> .gitignore <<'GITIGNORE'

# --- local forensic and generated artifact ignores ---
*.bak
*.bak.*
*.err
*.zip
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
reports/repo-hygiene/
# --- end local forensic and generated artifact ignores ---
GITIGNORE
  echo "UPDATED: .gitignore" | tee -a "$REPORT"
else
  echo "SKIPPED: .gitignore marker already exists" | tee -a "$REPORT"
fi

note "Finálny audit"
{
  echo
  echo "=== Status after archive actions ==="
  git status --short || true
  echo
  echo "=== Archived files ==="
  find "$ARCHIVE_DIR" -type f | sort || true
  echo
  echo "=== Proposed ops tools ==="
  find scripts/ops -maxdepth 1 -type f | sort || true
} | tee -a "$REPORT"

note "Voliteľný commit ops toolboxu"
echo "Commitnúť .gitignore, scripts/ops a scripts/archive? [yes/NO]"
read -r COMMIT_CONFIRM

if [ "$COMMIT_CONFIRM" = "yes" ]; then
  git add .gitignore scripts/ops scripts/archive
  echo
  echo "=== Staged changes ==="
  git diff --cached --stat
  echo
  echo "Vytvoriť commit? [yes/NO]"
  read -r FINAL_COMMIT

  if [ "$FINAL_COMMIT" = "yes" ]; then
    git commit -m "chore: organize repository operations and forensic archive"
    echo "Commit úspešne vytvorený." | tee -a "$REPORT"
  else
    echo "Zmeny sú staged, commit nebol vytvorený." | tee -a "$REPORT"
  fi
else
  echo "Žiadny commit nebol vytvorený." | tee -a "$REPORT"
fi

cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true

note "Hotovo"
echo "Report v projekte: $REPORT"
echo "Kópia v Download: $DOWNLOAD_DIR/$(basename "$REPORT")"
echo
echo "Aktuálny git stav:"
git status --short || true
