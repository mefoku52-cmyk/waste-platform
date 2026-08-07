#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
cd "${PROJECT_DIR}"
set -a
source "${ENV_FILE}"
set +a
if [ -z "${APP_DOMAIN:-}" ] || [ -z "${API_DOMAIN:-}" ] || [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
  echo "APP_DOMAIN, API_DOMAIN and LETSENCRYPT_EMAIL are required in ${ENV_FILE}"
exit 1
fi
docker compose --env-file "${ENV_FILE}" up -d nginx
docker compose --env-file "${ENV_FILE}" run --rm certbot certonly 
  --webroot -w /var/www/certbot -d "${APP_DOMAIN}" -d "${API_DOMAIN}" 
  --email "${LETSENCRYPT_EMAIL}" --agree-tos --no-eff-email
docker compose --env-file "${ENV_FILE}" restart nginx
echo "Let's Encrypt certificates issued and nginx restarted."
