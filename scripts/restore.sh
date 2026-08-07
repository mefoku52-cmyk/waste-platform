#!/bin/bash
set -Eeuo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup-directory>"
  exit 1
fi
BACKUP_DIR="$1"
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
if [ ! -d "${BACKUP_DIR}" ]; then
  echo "Backup directory not found: ${BACKUP_DIR}"
  exit 1
fi
cd "${PROJECT_DIR}"
set -a
source "${ENV_FILE}"
set +a
echo "[restore] restoring postgres"
cat "${BACKUP_DIR}/postgres.sql" | docker compose --env-file "${ENV_FILE}" exec -T postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
echo "[restore] done"
