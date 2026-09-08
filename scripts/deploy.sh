#!/usr/bin/env bash
set -euo pipefail

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

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || \
        error "$1 is not installed or not available in PATH"
}

if [ ! -f "${ENV_FILE}" ]; then
    error "Missing ${PROJECT_DIR}/${ENV_FILE}"
fi

require_cmd docker

if ! docker compose version >/dev/null 2>&1; then
    error "Docker Compose plugin is not available"
fi

if [ ! -f "${COMPOSE_FILE}" ]; then
    error "Missing ${PROJECT_DIR}/${COMPOSE_FILE}"
fi

RELEASE_ID="${RELEASE_ID:-}"
IMAGE_TAG="${IMAGE_TAG:-}"
REGISTRY_IMAGE_PREFIX="${REGISTRY_IMAGE_PREFIX:-}"

if [ -z "${RELEASE_ID}" ]; then
    error "RELEASE_ID is required"
fi

if [ -z "${IMAGE_TAG}" ]; then
    error "IMAGE_TAG is required"
fi

if [ -z "${REGISTRY_IMAGE_PREFIX}" ]; then
    error "REGISTRY_IMAGE_PREFIX is required"
fi

case "${REGISTRY_IMAGE_PREFIX}" in
    *latest*|*LATEST*|*dev*|*DEV*|*test*|*TEST*|*current*|*CURRENT*)
        error "Mutable or non-production registry prefix rejected"
        ;;
esac

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
STAGED_STATE="${RELEASE_STATE_DIR}/current-release.env.staged"

mkdir -p "${RELEASE_STATE_DIR}"

export RELEASE_ID
export IMAGE_TAG
export REGISTRY_IMAGE_PREFIX

log "=== RELEASE IDENTITY ==="
log "RELEASE_ID=${RELEASE_ID}"
log "IMAGE_TAG=${IMAGE_TAG}"
log "REGISTRY_IMAGE_PREFIX=${REGISTRY_IMAGE_PREFIX}"

log "=== COMPOSE CONFIG VALIDATION ==="

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    config >/dev/null

log "[OK] Compose configuration valid"

log "=== IMAGE PULL ==="

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    pull api web

log "[OK] Images pulled"

log "=== DEPLOY ==="

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    up -d --remove-orphans

log "[OK] Compose deployment command completed"

log "=== SERVICE VERIFICATION ==="

if ! docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    ps --status running --services >/dev/null 2>&1; then

    printf '[ERROR] Compose service status verification failed\n' >&2
    exit 1
fi

RUNNING_SERVICES="$(
    docker compose \
        --env-file "${ENV_FILE}" \
        -f "${COMPOSE_FILE}" \
        ps --status running --services 2>/dev/null || true
)"

printf '%s\n' "${RUNNING_SERVICES}"

for service in postgres redis api web; do
    if ! printf '%s\n' "${RUNNING_SERVICES}" | grep -qx "${service}"; then
        error "Required service is not running: ${service}"
    fi
done

log "[OK] All required services are running"

log "=== COMMIT RELEASE STATE ==="

if [ -f "${CURRENT_STATE}" ]; then
    cp -p "${CURRENT_STATE}" "${PREVIOUS_STATE}"
fi

cat > "${STAGED_STATE}" <<STATE_EOF
RELEASE_ID=${RELEASE_ID}
IMAGE_TAG=${IMAGE_TAG}
STATE_EOF

mv -f "${STAGED_STATE}" "${CURRENT_STATE}"

log "[OK] Release state committed"

printf '[OK] Deployment completed RELEASE_ID=%s IMAGE_TAG=%s\n' \
    "${RELEASE_ID}" "${IMAGE_TAG}"
