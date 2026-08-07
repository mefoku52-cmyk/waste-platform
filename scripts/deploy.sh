#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/data/data/com.termux/files/home/waste-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

cd "${PROJECT_DIR}"

if [ ! -f "${ENV_FILE}" ]; then
    echo "[ERROR] Missing ${PROJECT_DIR}/${ENV_FILE}" >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker is not installed or not available in PATH" >&2
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "[ERROR] Docker Compose plugin is not available" >&2
    exit 1
fi

set -a
. "./${ENV_FILE}"
set +a

if [ -f "infra/nginx/conf.d/default.conf.template" ]; then
    mkdir -p infra/nginx/conf.d

    if command -v envsubst >/dev/null 2>&1; then
        envsubst '${APP_DOMAIN} ${API_DOMAIN}' \
            < infra/nginx/conf.d/default.conf.template \
            > infra/nginx/conf.d/default.conf
    else
        echo "[WARN] envsubst is not installed; Nginx template was not rendered"
    fi
fi

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    config >/dev/null

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    up -d --build --remove-orphans

echo "[OK] Deployment completed"
