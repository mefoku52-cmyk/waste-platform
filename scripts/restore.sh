#!/bin/bash
set -Eeuo pipefail

# Restore a backup into postgres.
#
# Safety: refuses to restore into a database whose NAME or ADDRESS looks like
# production unless the caller passes an explicit confirmation argument
# (--confirm-production). Production markers are render hosts, dpg-* instance
# ids and the known production database names.

CONFIRM=""
if [ "${1:-}" = "--confirm-production" ]; then
  CONFIRM="--confirm-production"
  shift
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 [--confirm-production] <backup-directory>" >&2
  echo "  --confirm-production   required when the target name/address looks like production" >&2
  exit 1
fi

BACKUP_DIR="$1"
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [ ! -d "${BACKUP_DIR}" ]; then
  echo "Backup directory not found: ${BACKUP_DIR}" >&2
  exit 1
fi

cd "${PROJECT_DIR}"
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

TARGET_DB="${POSTGRES_DB:-}"
TARGET_HOST="${PGHOST:-${POSTGRES_HOST:-}}"
TARGET_URL="${DATABASE_URL:-}"

# Production markers: Render hosts, Render instance ids, known prod db names.
PROD_MARKERS=("render.com" "dpg-" "cmep" "waste-platform" "waste_platform")
LOOKS_LIKE_PROD=0
for marker in "${PROD_MARKERS[@]}"; do
  case "${TARGET_DB}${TARGET_HOST}${TARGET_URL}" in
    *"${marker}"*) LOOKS_LIKE_PROD=1 ;;
  esac
done

if [ "${LOOKS_LIKE_PROD}" -eq 1 ] && [ "${CONFIRM}" != "--confirm-production" ]; then
  echo "[restore] REFUSED: target looks like PRODUCTION" >&2
  echo "[restore]   POSTGRES_DB=${TARGET_DB:-<unset>}" >&2
  echo "[restore]   host=${TARGET_HOST:-<unset>}" >&2
  echo "[restore] Re-run with --confirm-production if you really mean it." >&2
  exit 2
fi

echo "[restore] restoring postgres (db=${TARGET_DB:-<unset>} host=${TARGET_HOST:-<unset>})"
cat "${BACKUP_DIR}/postgres.sql" | docker compose --env-file "${ENV_FILE}" exec -T postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
echo "[restore] done"
