#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/data/data/com.termux/files/home/waste-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

cd "${PROJECT_DIR}"

log() {
    printf '%s\n' "$*"
}

error() {
    printf '[ERROR] %s\n' "$*" >&2
    exit 1
}

if [ ! -f "${ENV_FILE}" ]; then
    error "Missing ${PROJECT_DIR}/${ENV_FILE}"
fi

if ! command -v docker >/dev/null 2>&1; then
    error "Docker is not installed or not available in PATH"
fi

if ! docker compose version >/dev/null 2>&1; then
    error "Docker Compose plugin is not available"
fi

if [ ! -f "${COMPOSE_FILE}" ]; then
    error "Missing ${PROJECT_DIR}/${COMPOSE_FILE}"
fi

RELEASE_ID="${RELEASE_ID:-}"
IMAGE_TAG="${IMAGE_TAG:-}"

if [ -z "${RELEASE_ID}" ]; then
    error "RELEASE_ID is required"
fi

if [ -z "${IMAGE_TAG}" ]; then
    error "IMAGE_TAG is required"
fi

case "${RELEASE_ID}" in
    *latest*|*LATEST*|*dev*|*DEV*|*test*|*TEST*|*current*|*CURRENT*)
        error "Mutable or non-production RELEASE_ID rejected"
        ;;
esac

case "${IMAGE_TAG}" in
    *latest*|*LATEST*|*dev*|*DEV*|*test*|*TEST*|*current*|*CURRENT*)
        error "Mutable or non-production IMAGE_TAG rejected"
        ;;
esac

if ! printf '%s\n' "${RELEASE_ID}" | grep -qE '^sha-[0-9a-fA-F]{7,64}$'; then
    error "RELEASE_ID must use sha-<hex> identity"
fi

if ! printf '%s\n' "${IMAGE_TAG}" | grep -qE '^release-[0-9a-fA-F]{7,64}$'; then
    error "IMAGE_TAG must use release-<hex> identity"
fi

RELEASE_STATE_DIR="${PROJECT_DIR}/.production-release/state"
CURRENT_STATE="${RELEASE_STATE_DIR}/current-release.env"
PREVIOUS_STATE="${RELEASE_STATE_DIR}/previous-release.env"

mkdir -p "${RELEASE_STATE_DIR}"

if [ -f "${CURRENT_STATE}" ]; then
    cp -p "${CURRENT_STATE}" "${PREVIOUS_STATE}"
fi

cat > "${CURRENT_STATE}" <<STATE_EOF
RELEASE_ID=${RELEASE_ID}
IMAGE_TAG=${IMAGE_TAG}
STATE_EOF

export RELEASE_ID
export IMAGE_TAG

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    config >/dev/null

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    build api web

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    up -d --remove-orphans

if ! docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    ps --status running --services >/dev/null 2>&1; then
    printf '[ERROR] Compose service status verification failed\n' >&2
    exit 1
fi

printf '[OK] Deployment completed RELEASE_ID=%s IMAGE_TAG=%s\n' \
    "${RELEASE_ID}" "${IMAGE_TAG}"
