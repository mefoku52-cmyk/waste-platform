#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.production-recovery}"
STATE_FILE="${STATE_FILE:-$STATE_DIR/previous-release.env}"
RELEASE_VALIDATOR="${RELEASE_VALIDATOR:-$PROJECT_ROOT/scripts/validate-release-identity.sh}"

DRY_RUN="${DRY_RUN:-1}"
ACTION="${1:-deploy}"

log() {
    printf '%s\n' "$*"
}

fail() {
    log "ERROR: $*" >&2
    exit 2
}

require_file() {
    [ -f "$1" ] || fail "required file missing: $1"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "required command missing: $1"
}

require_file "$COMPOSE_FILE"
require_file "$RELEASE_VALIDATOR"
require_command docker

mkdir -p "$STATE_DIR"
chmod 0700 "$STATE_DIR"

validate_release_identity() {
    RELEASE_ID="${RELEASE_ID:-}"
    IMAGE_TAG="${IMAGE_TAG:-}"

    [ -n "$RELEASE_ID" ] || fail "RELEASE_ID is required"
    [ -n "$IMAGE_TAG" ] || fail "IMAGE_TAG is required"

    case "$RELEASE_ID" in
        latest|dev|test|current)
            fail "mutable RELEASE_ID forbidden"
            ;;
    esac

    case "$IMAGE_TAG" in
        latest|dev|test|current)
            fail "mutable IMAGE_TAG forbidden"
            ;;
    esac

    "$RELEASE_VALIDATOR" >/dev/null
}

compose() {
    docker compose -f "$COMPOSE_FILE" "$@"
}

capture_previous_release() {
    local current_release current_image config_hash captured_at

    current_release="${CURRENT_RELEASE_ID:-}"
    current_image_tag="${CURRENT_IMAGE_TAG:-}"
    current_image="${CURRENT_IMAGE_REFERENCE:-}"

    if [ -z "$current_release" ]; then
        if [ -f "$STATE_FILE" ]; then
            current_release="$(
                awk -F= '
                    /^CURRENT_RELEASE_ID=/ {
                        print substr($0, index($0, "=") + 1)
                        exit
                    }
                ' "$STATE_FILE"
            )"
        fi
    fi

    config_hash="$(
        compose config 2>/dev/null |
        sha256sum |
        awk '{print $1}'
    )"

    captured_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

    cat > "$STATE_FILE" <<STATE
PREVIOUS_RELEASE_ID=${current_release}
PREVIOUS_IMAGE_TAG=${current_image_tag}
PREVIOUS_IMAGE_REFERENCE=${current_image}
PREVIOUS_CONFIG_HASH=${config_hash}
CAPTURED_AT=${captured_at}
STATE_FORMAT_VERSION=1
STATE

    chmod 0600 "$STATE_FILE"
}

load_previous_release() {
    [ -f "$STATE_FILE" ] || fail "previous release state is unavailable"

    PREVIOUS_RELEASE_ID="$(
        awk -F= '
            /^PREVIOUS_RELEASE_ID=/ {
                print substr($0, index($0, "=") + 1)
                exit
            }
        ' "$STATE_FILE"
    )"

    PREVIOUS_IMAGE_TAG="$(
        awk -F= '
            /^PREVIOUS_IMAGE_TAG=/ {
                print substr($0, index($0, "=") + 1)
                exit
            }
        ' "$STATE_FILE"
    )"

    PREVIOUS_IMAGE_REFERENCE="$(
        awk -F= '
            /^PREVIOUS_IMAGE_REFERENCE=/ {
                print substr($0, index($0, "=") + 1)
                exit
            }
        ' "$STATE_FILE"
    )"

    PREVIOUS_CONFIG_HASH="$(
        awk -F= '
            /^PREVIOUS_CONFIG_HASH=/ {
                print substr($0, index($0, "=") + 1)
                exit
            }
        ' "$STATE_FILE"
    )"

    [ -n "${PREVIOUS_RELEASE_ID:-}" ] ||
        fail "previous RELEASE_ID unavailable"

    [ -n "${PREVIOUS_IMAGE_TAG:-}" ] ||
        fail "previous IMAGE_TAG unavailable"

    printf '%s\n' "${PREVIOUS_IMAGE_TAG}" |
        grep -qE '^release-[0-9a-fA-F]{7,64}$' ||
        fail "previous IMAGE_TAG is invalid"

    [ -n "${PREVIOUS_IMAGE_REFERENCE:-}" ] ||
        fail "previous image artifact unavailable"

    [ -n "${PREVIOUS_CONFIG_HASH:-}" ] ||
        fail "previous configuration identity unavailable"

    case "$PREVIOUS_RELEASE_ID" in
        latest|dev|test|current)
            fail "previous release identity is mutable"
            ;;
    esac
}

health_check() {
    local attempt

    for attempt in 1 2 3 4 5; do
        if compose ps --all 2>/dev/null |
            grep -Eiq 'healthy|running'; then
            return 0
        fi

        if [ "$DRY_RUN" = "1" ]; then
            return 0
        fi

        sleep 3
    done

    return 1
}

deploy_release() {
    validate_release_identity
    capture_previous_release

    log "RELEASE_ID=${RELEASE_ID}"
    log "IMAGE_TAG=${IMAGE_TAG}"

    if [ "$DRY_RUN" = "1" ]; then
        log "DRY_RUN=1"
        log "DEPLOYMENT_NOT_EXECUTED"
        return 0
    fi

    compose pull
    compose up -d --remove-orphans

    if ! health_check; then
        log "DEPLOYMENT_HEALTH_FAILED"
        rollback_release
        fail "deployment failed and rollback path was required"
    fi

    log "DEPLOYMENT_HEALTH_OK"
}

rollback_release() {
    load_previous_release

    log "ROLLBACK_TO_RELEASE=${PREVIOUS_RELEASE_ID}"

    if [ "$DRY_RUN" = "1" ]; then
        log "DRY_RUN=1"
        log "ROLLBACK_NOT_EXECUTED"
        return 0
    fi

    if ! docker image inspect "$PREVIOUS_IMAGE_REFERENCE" >/dev/null 2>&1; then
        fail "previous release artifact is not locally available"
    fi

    export IMAGE_TAG="$PREVIOUS_IMAGE_TAG"
    export RELEASE_ID="$PREVIOUS_RELEASE_ID"

    compose up -d --remove-orphans

    if ! health_check; then
        fail "rollback health verification failed"
    fi

    log "ROLLBACK_HEALTH_OK"
}

case "$ACTION" in
    validate)
        validate_release_identity
        log "RELEASE_IDENTITY_VALID=1"
        ;;
    capture)
        capture_previous_release
        log "PREVIOUS_RELEASE_STATE_CAPTURED=1"
        ;;
    deploy)
        deploy_release
        ;;
    rollback)
        rollback_release
        ;;
    *)
        fail "unsupported action: $ACTION"
        ;;
esac
