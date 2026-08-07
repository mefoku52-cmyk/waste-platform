#!/bin/bash
set -Eeuo pipefail
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
BACKUP_ROOT="${BACKUP_ROOT:-${PROJECT_DIR}/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"
cd "${PROJECT_DIR}"
set -a
source "${ENV_FILE}"
set +a
echo "[backup] creating backup directory ${BACKUP_DIR}"
echo "[backup] backing up postgres"
docker compose --env-file "${ENV_FILE}" exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > "${BACKUP_DIR}/postgres.sql"
echo "[backup] done: ${BACKUP_DIR}"
