#!/usr/bin/env bash
set -Eeuo pipefail

# Obnova PostgreSQL zalohy.
# Bezpecnost: ak cielova databaza vyzera ako PRODUKCNA, skript obnovu ODMIETNE,
# pokial nie je explicitne zadany argument --confirm-production.
# Tento skript sa NIKDY nesmie spustat proti produkcii bez vedomeho rozhodnutia.

usage() {
  cat >&2 <<'EOF'
Usage: restore.sh <backup-file|backup-directory> [--confirm-production]

  Obnovi PostgreSQL dump.
  <backup-directory>  ocakava <dir>/postgres.sql (alebo .sql.gz)
  <backup-file>       priamo .sql alebo .sql.gz
  --confirm-production  vyzaduje sa, ak ciel vyzera ako produkcia.

Prikazy na porovnanie:
  SOURCE_TABLES / TARGET_TABLES / DIFF sa vypisu na konci.
EOF
}

CONFIRM_PRODUCTION=0
INPUTS=()
for arg in "$@"; do
  case "$arg" in
    --confirm-production) CONFIRM_PRODUCTION=1 ;;
    -h|--help) usage; exit 0 ;;
    *) INPUTS+=("$arg") ;;
  esac
done

if [ "${#INPUTS[@]}" -lt 1 ]; then
  usage
  exit 1
fi

BACKUP_INPUT="${INPUTS[0]}"
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

# --- 1. Najdi dump ---
DUMP=""
if [ -d "$BACKUP_INPUT" ]; then
  for candidate in "$BACKUP_INPUT/postgres.sql" "$BACKUP_INPUT/postgres.sql.gz"; do
    [ -f "$candidate" ] && DUMP="$candidate" && break
  done
else
  DUMP="$BACKUP_INPUT"
fi
if [ -z "$DUMP" ] || [ ! -f "$DUMP" ]; then
  echo "[restore] ERROR: backup not found: $BACKUP_INPUT" >&2
  exit 1
fi

# --- 2. Nacitaj cielovu konfiguraciu (NIKDY nevypisovat obsah env) ---
# Env sa cita IBA z PROJECT_DIR, nikdy z aktualneho adresara.
if [ -d "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/$ENV_FILE" ]; then
  cd "$PROJECT_DIR"
  set -a
  # shellcheck disable=SC1090
  . "./$ENV_FILE"
  set +a
fi

DB_NAME="${POSTGRES_DB:-}"
DB_HOST="${POSTGRES_HOST:-${PGHOST:-}}"
DB_URL="${DATABASE_URL:-}"
PROD_SIGNATURE="${DB_NAME} ${DB_HOST} ${DB_URL}"

# --- 3. Detekcia produkcie ---
IS_PROD=0
case "$PROD_SIGNATURE" in
  *render.com*|*dpg-*|*waste-platform-db*|*oregon*|*frankfurt*|*ohio*) IS_PROD=1 ;;
esac
case "$DB_NAME" in
  cmep|cmep_prod|cmep-platform|waste-platform|waste_platform|production|prod) IS_PROD=1 ;;
esac

if [ "$IS_PROD" = "1" ] && [ "$CONFIRM_PRODUCTION" != "1" ]; then
  echo "[restore] REFUSED: cielova databaza vyzera ako PRODUKCNA." >&2
  echo "[restore]   db=${DB_NAME:-?} host=${DB_HOST:-?}" >&2
  echo "[restore]   Ak je to naozaj zamyslene, spusti s --confirm-production." >&2
  exit 3
fi

if [ "$IS_PROD" = "1" ]; then
  echo "[restore] WARNING: obnovujes do databazy, ktora vyzera ako PRODUKCNA." >&2
fi

# --- 4. Cielovy prikaz ---
restore_target() {
  if [ -f "$COMPOSE_FILE" ] && [ -n "${POSTGRES_USER:-}" ] && [ -n "${POSTGRES_DB:-}" ]; then
    docker compose --env-file "$ENV_FILE" exec -T postgres \
      psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" "$@"
  elif [ -n "$DB_URL" ]; then
    psql "$DB_URL" "$@"
  else
    echo "[restore] ERROR: ziadny ciel (POSTGRES_USER/DB alebo DATABASE_URL)." >&2
    return 1
  fi
}

# --- 5. Obnova ---
echo "[restore] restoring from $DUMP"
if [ "${DUMP##*.}" = "gz" ]; then
  gunzip -c "$DUMP" | restore_target
else
  restore_target < "$DUMP"
fi
echo "[restore] done"

# --- 6. Porovnanie poctu tabuliek zdroj vs ciel ---
SOURCE_TABLES=$(
  if [ "${DUMP##*.}" = "gz" ]; then gunzip -c "$DUMP"; else cat "$DUMP"; fi \
    | grep -c "^CREATE TABLE" || true
)
TARGET_TABLES=$(restore_target -tAc \
  "select count(*) from information_schema.tables where table_schema='public' and table_type='BASE TABLE'" 2>/dev/null || echo "?")
echo "[restore] SOURCE_TABLES=$SOURCE_TABLES"
echo "[restore] TARGET_TABLES=$TARGET_TABLES"
if [ "$TARGET_TABLES" != "?" ]; then
  echo "[restore] DIFF=$(( TARGET_TABLES - SOURCE_TABLES ))"
  echo "[restore] poznamka: rozdiel vzniká, ak DB obsahuje tabulky mimo Alembic"
  echo "          (napr. activity_events / admin_audit_entries z raw SQL), alebo"
  echo "          ak dump vznikal v inom case nez aktualny stav schemy."
fi
exit 0
