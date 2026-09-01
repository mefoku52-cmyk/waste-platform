#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
STAMP="$(date '+%Y%m%d-%H%M%S')"
REPORT_DIR="$PROJECT/reports/repo-hygiene"
REPORT="$REPORT_DIR/untracked-tools-audit-$STAMP.txt"
DOWNLOAD_DIR="$HOME/storage/shared/Download"

cd "$PROJECT"
mkdir -p "$REPORT_DIR" "$DOWNLOAD_DIR"

say() {
  printf '\n==> %s\n' "$*"
}

exists() {
  [ -e "$1" ]
}

file_header() {
  local path="$1"
  {
    echo
    echo "================================================================"
    echo "FILE: $path"
    echo "----------------------------------------------------------------"
    if [ -f "$path" ]; then
      ls -lh "$path"
      echo
      echo "--- first 80 lines ---"
      sed -n '1,80p' "$path" 2>/dev/null || true
    elif [ -d "$path" ]; then
      echo "[directory]"
      find "$path" -maxdepth 3 \( -type f -o -type d \) | sort | sed -n '1,200p'
    else
      echo "[missing]"
    fi
  } >> "$REPORT"
}

classify_line() {
  local bucket="$1"
  local path="$2"
  printf '%s: %s\n' "$bucket" "$path" >> "$REPORT"
}

: > "$REPORT"
{
  echo "Remaining untracked tools audit"
  echo "Generated: $(date -Iseconds)"
  echo "Project: $PROJECT"
  echo
  echo "=== Current git status --short ==="
  git status --short || true
} >> "$REPORT"

ROOT_SCRIPTS=(
  "app/start_app.sh"
  "check-db-content.sh"
  "fix_auth_complete.sh"
  "inspect-cmep-backups.sh"
  "inspect-db-schema.sh"
  "run-check.sh"
)

WEB_SCRIPTS=(
  "apps/web/fix-imports-and-eslint.sh"
  "apps/web/fix-now.sh"
  "apps/web/fix_cryptography.sh"
  "apps/web/refactor-cmep-fix.sh"
  "apps/web/refactor-cmep.sh"
  "apps/web/rewrite-imports-node.mjs"
  "apps/web/rewrite-imports-sed.sh"
  "apps/web/eslint"
)

WEB_FILES=(
  "apps/web/src/cmep-dark.css"
)

DIRS=(
  "_local_archive"
  "scripts/archive"
  "scripts/fixes/backend"
)

say "Zapisujem súhrn statusu"
{
  echo
  echo "=== Untracked only ==="
  git ls-files --others --exclude-standard | sort || true
} >> "$REPORT"

say "Audit root scriptov"
for path in "${ROOT_SCRIPTS[@]}"; do
  file_header "$path"
done

say "Audit web scriptov"
for path in "${WEB_SCRIPTS[@]}"; do
  file_header "$path"
done

say "Audit web súborov"
for path in "${WEB_FILES[@]}"; do
  file_header "$path"
done

say "Audit adresárov"
for path in "${DIRS[@]}"; do
  file_header "$path"
done

say "Klasifikačné pravidlá"
{
  echo
  echo "=== Proposed classification ==="
} >> "$REPORT"

for path in "${ROOT_SCRIPTS[@]}"; do
  if exists "$path"; then
    case "$path" in
      app/start_app.sh|run-check.sh|check-db-content.sh|inspect-db-schema.sh)
        classify_line "REVIEW-KEEP-CANDIDATE" "$path"
        ;;
      fix_auth_complete.sh|inspect-cmep-backups.sh)
        classify_line "ARCHIVE-OR-KEEP-IF-STILL-USED" "$path"
        ;;
      *)
        classify_line "REVIEW" "$path"
        ;;
    esac
  fi
done

for path in "${WEB_SCRIPTS[@]}"; do
  if exists "$path"; then
    case "$path" in
      apps/web/rewrite-imports-node.mjs|apps/web/rewrite-imports-sed.sh)
        classify_line "KEEP-IF-ACTIVE-REFACTOR-TOOL" "$path"
        ;;
      apps/web/refactor-cmep.sh|apps/web/refactor-cmep-fix.sh)
        classify_line "REVIEW-HIGH-VALUE" "$path"
        ;;
      apps/web/fix-imports-and-eslint.sh|apps/web/fix-now.sh|apps/web/fix_cryptography.sh)
        classify_line "ARCHIVE-ONE-OFF-REPAIR" "$path"
        ;;
      apps/web/eslint)
        classify_line "DROP-OR-INSPECT-BINARYISH-ARTIFACT" "$path"
        ;;
      *)
        classify_line "REVIEW" "$path"
        ;;
    esac
  fi
done

for path in "${WEB_FILES[@]}"; do
  if exists "$path"; then
    classify_line "KEEP-ONLY-IF-IMPORTED-BY-APP" "$path"
  fi
done

for path in "${DIRS[@]}"; do
  if exists "$path"; then
    case "$path" in
      _local_archive)
        classify_line "KEEP-LOCAL-UNTRACKED" "$path"
        ;;
      scripts/archive)
        classify_line "REVIEW-MIXED-ARCHIVE" "$path"
        ;;
      scripts/fixes/backend)
        classify_line "REVIEW-POSSIBLE-TOOLBOX" "$path"
        ;;
      *)
        classify_line "REVIEW" "$path"
        ;;
    esac
  fi
done

say "Heuristiky grep"
{
  echo
  echo "=== Shebang scan ==="
  grep -RIn '^#!' app/start_app.sh check-db-content.sh fix_auth_complete.sh inspect-cmep-backups.sh inspect-db-schema.sh run-check.sh apps/web 2>/dev/null | sed -n '1,200p'
  echo
  echo "=== Dangerous operations scan ==="
  grep -RInE '\brm -rf\b|\bgit clean\b|\bdrop database\b|\bdocker compose down -v\b|\balembic downgrade\b|\bmv .*cleanup_archive\b' \
    app/start_app.sh check-db-content.sh fix_auth_complete.sh inspect-cmep-backups.sh inspect-db-schema.sh run-check.sh apps/web scripts/fixes/backend 2>/dev/null | sed -n '1,200p'
  echo
  echo "=== Entry usage scan for cmep-dark.css ==="
  grep -RIn 'cmep-dark.css' apps/web/src apps/web 2>/dev/null | sed -n '1,80p'
  echo
  echo "=== Barrel export usage hints ==="
  find apps/web/src/features -maxdepth 2 -name 'index.ts' | sort 2>/dev/null
} >> "$REPORT"

say "Odporúčaný ďalší krok"
cat >> "$REPORT" <<'NEXTSTEP'

=== Recommended next action ===
1. Prečítaj klasifikáciu KEEP / ARCHIVE / DROP / REVIEW.
2. Ak chceš, v ďalšom kroku spravíme JEDEN skript, ktorý:
   - presunie ARCHIVE položky do _local_archive/manual-archive-<timestamp>/,
   - ponechá KEEP kandidátov,
   - a pripraví presné git add príkazy len pre hodnotné utility.
3. Tento audit nič necommituje a nič nemaže.

NEXTSTEP

cp -f "$REPORT" "$DOWNLOAD_DIR/" 2>/dev/null || true

say "Hotovo"
echo "Report: $REPORT"
echo "Download: $DOWNLOAD_DIR/$(basename "$REPORT")"
echo
echo "Pozri si:"
echo "sed -n '1,320p' \"$REPORT\""
