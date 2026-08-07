#!/bin/bash
set -Eeuo pipefail
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
cd "${PROJECT_DIR}"
echo "[health] docker compose ps"
docker compose --env-file "${ENV_FILE}" ps
echo "[health] api"
curl -fsSL "${API_HEALTH_URL:-https://api.example.com/health}" >/dev/null && echo "api ok" || echo "api failed"
echo "[health] frontend"
curl -fsSL "${APP_HEALTH_URL:-https://app.example.com}" >/dev/null && echo "frontend ok" || echo "frontend failed"
