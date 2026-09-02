#!/usr/bin/env bash
# =============================================================================
# waste-platform-finale-hygiene.sh
# =============================================================================
# Uzavrie hygienu z extreme auditu.
# Rieši: 31 GB audit súbory, audit-output, .env backupy, untrack secretov,
# .gitignore, duplicitné compose/Dockerfile/docs, phase7 skripty na koreni,
# leftover apps/t a waste.db.
# Nerieši: runtime logiku, rotáciu secretov na serveri, prepis git histórie,
# green testy, zlučenie origin/main.
# =============================================================================
set -euo pipefail

APPLY="${APPLY:-0}"
PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
STAMP="$(date +%Y%m%d_%H%M%S)"
QUARANTINE="$PROJECT_ROOT/_quarantine/$STAMP"
LOG="$QUARANTINE/hygiene.log"

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
log() { printf '%s\n' "$*" | tee -a "$LOG"; }

is_waste_platform() {
  [[ -d "$PROJECT_ROOT/app" && -d "$PROJECT_ROOT/apps" && -f "$PROJECT_ROOT/README.md" ]]
}

qmove() {
  local src="$1"
  local rel="${src#"$PROJECT_ROOT"/}"
  local dest="$QUARANTINE/moved/$rel"
  [[ -e "$src" || -L "$src" ]] || return 0
  if [[ "$APPLY" != "1" ]]; then
    log "DRY-RUN move  $rel"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  mv "$src" "$dest"
  log "MOVED         $rel"
}

qrm_dir_if_generated() {
  local src="$1"
  local rel="${src#"$PROJECT_ROOT"/}"
  [[ -e "$src" ]] || return 0
  if [[ "$APPLY" != "1" ]]; then
    log "DRY-RUN rm -rf $rel"
    return 0
  fi
  rm -rf "$src"
  log "REMOVED       $rel"
}

untrack_if_tracked() {
  local rel="$1"
  [[ -d "$PROJECT_ROOT/.git" ]] || return 0
  if git -C "$PROJECT_ROOT" ls-files --error-unmatch "$rel" >/dev/null 2>&1; then
    if [[ "$APPLY" != "1" ]]; then
      log "DRY-RUN git rm --cached -- $rel"
      return 0
    fi
    git -C "$PROJECT_ROOT" rm -r --cached --ignore-unmatch -- "$rel" >/dev/null
    log "UNTRACKED     $rel"
  fi
}

ensure_gitignore_block() {
  local gi="$PROJECT_ROOT/.gitignore"
  if [[ "$APPLY" != "1" ]]; then
    log "DRY-RUN would merge hygiene block into .gitignore"
    return 0
  fi
  touch "$gi"
  if grep -q 'waste-platform hygiene contract' "$gi" 2>/dev/null; then
    log "GITIGNORE     hygiene block already present"
    return 0
  fi
  cat >> "$gi" <<'GI'

# === waste-platform hygiene contract ===
.venv/
**/.venv/
**/__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.mypy_cache/

node_modules/
apps/web/node_modules/
apps/web/.next/
apps/web/out/
apps/web/tsconfig.tsbuildinfo

.env
.env.*
!.env.example
!**/.env.example
apps/web/.env.local
apps/web/.env*.local
.env.production
.env.compose

audit-output/
_quarantine/
*.bak
*.bak.*
*.before
*.before-*
*.after
*.old
*.unused_duplicate
*.pre-remediation
*.legacy

.backup/
.fix-backup-*/
.schema-authority-backup-*/
manual-restore-backups/

waste.db
*.log
logs/
frontend.log

phase7*.sh
phase74*.sh
phase7_*.sh

FINAL-AUTHORITY-AUDIT*.txt
FINAL-SCHEMA-AUTHORITY-DIFF*.txt
STEP-09-SCHEMA-PROVENANCE-AUDIT*.txt
fix_report.txt
audit_report.json
GI
  log "GITIGNORE     appended hygiene contract"
}

write_env_example() {
  local dest="$PROJECT_ROOT/.env.example"
  if [[ "$APPLY" != "1" ]]; then
    log "DRY-RUN would write .env.example if missing"
    return 0
  fi
  if [[ -f "\( dest" ]] && [[ " \)(wc -c < "$dest")" -gt 80 ]]; then
    log "KEEP          .env.example"
    return 0
  fi
  cat > "$dest" <<'ENV'
# Canonical environment contract. Copy to an untracked .env locally.
# Never commit real values.

APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

DATABASE_URL=postgresql+asyncpg://waste:change-me@127.0.0.1:5432/waste
REDIS_URL=redis://127.0.0.1:6379/0

JWT_SECRET=change-me-to-a-long-random-value
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600

CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
ENV
  log "WROTE         .env.example"
}

write_canon_note() {
  if [[ "$APPLY" != "1" ]]; then
    log "DRY-RUN would write docs/AUTHORITY.md"
    return 0
  fi
  mkdir -p "$PROJECT_ROOT/docs"
  cat > "$PROJECT_ROOT/docs/AUTHORITY.md" <<'MD'
# Authority contract

| Concern | Canonical path | Everything else |
|---|---|---|
| Backend app | `app/` | no second backend tree |
| Frontend app | `apps/web/` | ignore `apps/t` |
| Env contract | `.env.example` | real values only in untracked `.env` |
| Compose | `docker-compose.yml` | backups in `_quarantine` |
| Backend image | `docker/backend/Dockerfile` | inner `app/Dockerfile` archived |
| Frontend image | `docker/frontend/Dockerfile` | inner `apps/web/Dockerfile` archived |
| Migrations | `alembic/` + `alembic.ini` | do not grow a second tree |
| Deploy docs | `docs/deployment.md` | no parallel `DEPLOYMENT.md` |
| Forensic scripts | `scripts/forensics/archive/` | not repository root |
| Generated audits | `_quarantine/` | never live `audit-output/` |

Rotate every secret that ever lived in `.env*`, README or compose.
This script does not rewrite git history.
MD
  log "WROTE         docs/AUTHORITY.md"
}

main() {
  mkdir -p "$QUARANTINE/moved"
  : > "$LOG"
  log "PROJECT_ROOT=$PROJECT_ROOT"
  log "APPLY=$APPLY"
  is_waste_platform || die "Set PROJECT_ROOT to waste-platform root."
  command -v git >/dev/null 2>&1 || die "git not found"

  qrm_dir_if_generated "$PROJECT_ROOT/audit-output"
  qrm_dir_if_generated "$PROJECT_ROOT/apps/web/node_modules"
  qrm_dir_if_generated "$PROJECT_ROOT/apps/web/.next"
  qrm_dir_if_generated "$PROJECT_ROOT/.venv"
  qrm_dir_if_generated "$PROJECT_ROOT/apps/web/.venv"
  qrm_dir_if_generated "$PROJECT_ROOT/scripts/dev/backend_test_env"
  qrm_dir_if_generated "$PROJECT_ROOT/.pytest_cache"
  qrm_dir_if_generated "$PROJECT_ROOT/.ruff_cache"

  local f
  for f in \
    .env.backup.20260824-092956 \
    .env.before-newline-fix.20260817-120730 \
    .env.compose \
    .env.dedup.20260817-120833 \
    .env.finalbak.20260817-131129 \
    .env.fixbak.20260817-115715
  do
    qmove "$PROJECT_ROOT/$f"
  done

  untrack_if_tracked ".env"
  untrack_if_tracked ".env.production"
  untrack_if_tracked "apps/web/.env.local"
  untrack_if_tracked "waste.db"
  untrack_if_tracked "frontend.log"

  qmove "$PROJECT_ROOT/.backup"
  qmove "$PROJECT_ROOT/.fix-backup-20260821-161259"
  qmove "$PROJECT_ROOT/.fix-backup-20260821-161720"
  qmove "$PROJECT_ROOT/.fix-backup-20260821-162333"
  qmove "$PROJECT_ROOT/.fix-backup-20260823-235334"
  qmove "$PROJECT_ROOT/.fix-backup-20260824-085054"
  qmove "$PROJECT_ROOT/.schema-authority-backup-20260824-011051"
  qmove "$PROJECT_ROOT/.schema-authority-backup-20260824-012856"
  qmove "$PROJECT_ROOT/manual-restore-backups"
  qmove "$PROJECT_ROOT/docker-compose.yml.backend-frontend-variant-20260808-011656"
  qmove "$PROJECT_ROOT/docker-compose.yml.bak.20260826-202603"
  qmove "$PROJECT_ROOT/docker-compose.yml.bak.20260826-203145"
  qmove "$PROJECT_ROOT/docker-compose.yml.bak.20260826-203430"
  qmove "$PROJECT_ROOT/app/Dockerfile"
  qmove "$PROJECT_ROOT/apps/web/Dockerfile"
  qmove "$PROJECT_ROOT/docs/DEPLOYMENT.md"
  qmove "$PROJECT_ROOT/apps/t"
  qmove "$PROJECT_ROOT/waste.db"
  qmove "$PROJECT_ROOT/FINAL-AUTHORITY-AUDIT-20260824-010845.txt"
  qmove "$PROJECT_ROOT/FINAL-AUTHORITY-AUDIT-20260824-012955.txt"
  qmove "$PROJECT_ROOT/FINAL-SCHEMA-AUTHORITY-DIFF-20260824-010307.txt"
  qmove "$PROJECT_ROOT/FINAL-SCHEMA-AUTHORITY-DIFF-20260824-080000.txt"
  qmove "$PROJECT_ROOT/STEP-09-SCHEMA-PROVENANCE-AUDIT-20260824-011409.txt"
  qmove "$PROJECT_ROOT/fix_report.txt"
  qmove "$PROJECT_ROOT/audit_report.json"
  qmove "$PROJECT_ROOT/frontend.log"
  qmove "$PROJECT_ROOT/.coverage"

  if [[ "$APPLY" == "1" ]]; then
    mkdir -p "$PROJECT_ROOT/scripts/forensics/archive"
  else
    log "DRY-RUN would create scripts/forensics/archive"
  fi

  local script
  for script in \
    "$PROJECT_ROOT"/phase7*.sh \
    "$PROJECT_ROOT"/phase74*.sh \
    "$PROJECT_ROOT"/CONSOLIDATE-SCHEMA-AUTHORITY.sh \
    "$PROJECT_ROOT"/FINAL-AUTHORITY-AUDIT.sh \
    "$PROJECT_ROOT"/FINAL-SCHEMA-AUTHORITY-DIFF.sh \
    "$PROJECT_ROOT"/PHASE2_CONFIGURATION_FORENSICS.sh \
    "$PROJECT_ROOT"/clean_tracked_archive_from_git.sh \
    "$PROJECT_ROOT"/extreme_whole_project_audit.sh \
    "$PROJECT_ROOT"/finalize_repo_hygiene.sh \
    "$PROJECT_ROOT"/waste-platform-extreme-audit.sh \
    "$PROJECT_ROOT"/auto_fix_audit.py
  do
    [[ -e "$script" ]] || continue
    local base
    base="$(basename "$script")"
    if [[ "$APPLY" != "1" ]]; then
      log "DRY-RUN archive script $base"
      continue
    fi
    mv "$script" "$PROJECT_ROOT/scripts/forensics/archive/$base"
    log "ARCHIVED      scripts/forensics/archive/$base"
  done

  ensure_gitignore_block
  write_env_example
  write_canon_note

  log ""
  log "DONE APPLY=$APPLY"
  log "Quarantine: $QUARANTINE"
  log "MANUAL NEXT:"
  log "  1. Rotate every secret that lived in .env* or README."
  log "  2. Review dirty source: config.py jwt_service.py listing-form.tsx http.ts config.ts"
  log "  3. Decide push of local main vs reset to origin/main."
  log "  4. Recreate one venv + one node_modules, then pytest and next build."
}

main "$@"
