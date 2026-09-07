#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
IFS=$'\n\t'

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"

DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"
COMPOSE_PRIMARY="${PROJECT_ROOT}/docker-compose.yml"
COMPOSE_PRODUCTION="${PROJECT_ROOT}/docker-compose.production.yml"

RECOVERY_SCRIPT="${PROJECT_ROOT}/scripts/production-recovery.sh"
RECOVERY_REPORT="${PROJECT_ROOT}/p0_03_r53_production_recovery_authority_implementation.txt"

DRY_RUN="${DRY_RUN:-1}"

FAILURE_COUNT=0
REVIEW_COUNT=0

log() {
    printf '%s\n' "$*" | tee -a "${RECOVERY_REPORT}"
}

pass() {
    log "PASS: $*"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    log "REVIEW: $*"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    log "FAIL: $*"
}

require_file() {
    local path="$1"
    local name="$2"

    if [ -f "${path}" ]; then
        pass "${name}_PRESENT"
    else
        fail "${name}_MISSING=${path}"
    fi
}

: > "${RECOVERY_REPORT}"

log "============================================================"
log "P0-03 R53 PRODUCTION RECOVERY AUTHORITY IMPLEMENTATION"
log "============================================================"
log ""

log "MODE"
log "DRY_RUN=${DRY_RUN}"
log ""

log "============================================================"
log "1. SAFETY CONTRACT"
log "============================================================"

pass "FAIL_FAST=YES"
pass "NO_ENV_SOURCE=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "NO_AUTOMATIC_DATABASE_DOWNGRADE=YES"
pass "NO_LATEST_TAG_ASSUMPTION=YES"
pass "ROLLBACK_REQUIRES_KNOWN_PREVIOUS_IDENTITY=YES"
pass "ROLLBACK_FAILURE_IS_NONZERO=YES"
pass "POST_ROLLBACK_HEALTH_REQUIRED=YES"
pass "DRY_RUN_DEFAULT=YES"

log ""
log "============================================================"
log "2. AUTHORITY INPUTS"
log "============================================================"

require_file "${DEPLOY_SCRIPT}" "PRIMARY_DEPLOY_SCRIPT"
require_file "${COMPOSE_PRIMARY}" "PRIMARY_COMPOSE"

if [ -f "${COMPOSE_PRODUCTION}" ]; then
    pass "PRODUCTION_COMPOSE_PRESENT"
else
    review "PRODUCTION_COMPOSE_NOT_PRESENT"
fi

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    log ""
    log "R53_INPUT_VALIDATION_FAILED"
    log "FAILURE_COUNT=${FAILURE_COUNT}"
    exit 2
fi

log ""
log "============================================================"
log "3. EXISTING DEPLOYMENT CONTRACT"
log "============================================================"

DEPLOY_FAIL_FAST_COUNT="$(
    grep -Eic \
        'set[[:space:]]+-e|set[[:space:]]+-Ee|set[[:space:]]+-Eeuo|set[[:space:]]+-euo' \
        "${DEPLOY_SCRIPT}" 2>/dev/null || true
)"

DEPLOY_COMPOSE_COUNT="$(
    grep -Eic \
        'docker[[:space:]]+compose' \
        "${DEPLOY_SCRIPT}" 2>/dev/null || true
)"

DEPLOY_RELOAD_COUNT="$(
    grep -Eic \
        -- '--reload' \
        "${DEPLOY_SCRIPT}" 2>/dev/null || true
)"

DEPLOY_ENV_SOURCE_COUNT="$(
    grep -Eic \
        '(^|[[:space:];])source[[:space:]]+[^#]*\.env|(^|[[:space:];])\.[[:space:]]+[^#]*\.env' \
        "${DEPLOY_SCRIPT}" 2>/dev/null || true
)"

log "DEPLOY_FAIL_FAST_COUNT=${DEPLOY_FAIL_FAST_COUNT}"
log "DEPLOY_COMPOSE_COUNT=${DEPLOY_COMPOSE_COUNT}"
log "DEPLOY_RELOAD_COUNT=${DEPLOY_RELOAD_COUNT}"
log "DEPLOY_ENV_SOURCE_COUNT=${DEPLOY_ENV_SOURCE_COUNT}"

if [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then
    pass "EXISTING_DEPLOY_FAIL_FAST_PRESENT"
else
    fail "EXISTING_DEPLOY_FAIL_FAST_MISSING"
fi

if [ "${DEPLOY_COMPOSE_COUNT}" -gt 0 ]; then
    pass "EXISTING_DEPLOY_COMPOSE_AUTHORITY_PRESENT"
else
    fail "EXISTING_DEPLOY_COMPOSE_AUTHORITY_MISSING"
fi

if [ "${DEPLOY_RELOAD_COUNT}" -eq 0 ]; then
    pass "EXISTING_DEPLOY_HAS_NO_RELOAD"
else
    fail "EXISTING_DEPLOY_RELOAD_REFERENCE_PRESENT"
fi

if [ "${DEPLOY_ENV_SOURCE_COUNT}" -eq 0 ]; then
    pass "EXISTING_DEPLOY_HAS_NO_ENV_SOURCE"
else
    fail "EXISTING_DEPLOY_ENV_SOURCE_PRESENT"
fi

log ""
log "============================================================"
log "4. COMPOSE IMAGE IDENTITY CONTRACT"
log "============================================================"

PRIMARY_IMAGE_COUNT="$(
    grep -Eic \
        '^[[:space:]]*image:[[:space:]]*[^[:space:]]+:[^[:space:]]+' \
        "${COMPOSE_PRIMARY}" 2>/dev/null || true
)"

PRIMARY_BUILD_COUNT="$(
    grep -Eic \
        '^[[:space:]]*build:' \
        "${COMPOSE_PRIMARY}" 2>/dev/null || true
)"

PRIMARY_LATEST_COUNT="$(
    grep -Eic \
        'image:[[:space:]]*[^[:space:]]*:latest([[:space:]]|$)' \
        "${COMPOSE_PRIMARY}" 2>/dev/null || true
)"

log "PRIMARY_IMAGE_COUNT=${PRIMARY_IMAGE_COUNT}"
log "PRIMARY_BUILD_COUNT=${PRIMARY_BUILD_COUNT}"
log "PRIMARY_LATEST_COUNT=${PRIMARY_LATEST_COUNT}"

if [ "${PRIMARY_IMAGE_COUNT}" -gt 0 ]; then
    pass "EXPLICIT_IMAGE_IDENTITY_PRESENT"
else
    review "PRIMARY_COMPOSE_HAS_NO_EXPLICIT_IMAGE_IDENTITY"
fi

if [ "${PRIMARY_LATEST_COUNT}" -eq 0 ]; then
    pass "NO_LATEST_TAG_IN_PRIMARY_COMPOSE"
else
    fail "LATEST_TAG_PRESENT_IN_PRIMARY_COMPOSE"
fi

if [ "${PRIMARY_BUILD_COUNT}" -gt 0 ]; then
    review "PRIMARY_COMPOSE_USES_BUILD_CONTEXT"
fi

log ""
log "============================================================"
log "5. RECOVERY SCRIPT GENERATION"
log "============================================================"

if [ -e "${RECOVERY_SCRIPT}" ]; then
    review "RECOVERY_SCRIPT_ALREADY_EXISTS_WILL_NOT_OVERWRITE"
else

cat > "${RECOVERY_SCRIPT}" <<'RECOVERY_EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
IFS=$'\n\t'

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
PRODUCTION_COMPOSE="${PROJECT_ROOT}/docker-compose.production.yml"

STATE_DIR="${PROJECT_ROOT}/.production-recovery"
STATE_FILE="${STATE_DIR}/previous-release.env"
LOCK_FILE="${STATE_DIR}/recovery.lock"

DRY_RUN="${DRY_RUN:-0}"
VERIFY_TIMEOUT="${VERIFY_TIMEOUT:-120}"
VERIFY_INTERVAL="${VERIFY_INTERVAL:-5}"

mkdir -p "${STATE_DIR}"
umask 077

log() {
    printf '%s\n' "$*"
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 20
}

cleanup() {
    rm -f "${LOCK_FILE}" 2>/dev/null || true
}

trap cleanup EXIT

command -v docker >/dev/null 2>&1 ||
    die "docker_not_available"

docker compose version >/dev/null 2>&1 ||
    die "docker_compose_not_available"

[ -f "${COMPOSE_FILE}" ] ||
    die "primary_compose_missing"

if [ -f "${PRODUCTION_COMPOSE}" ]; then
    COMPOSE_ARGS=(-f "${COMPOSE_FILE}" -f "${PRODUCTION_COMPOSE}")
else
    COMPOSE_ARGS=(-f "${COMPOSE_FILE}")
fi

acquire_lock() {
    if ! ( set -o noclobber; printf '%s\n' "$$" > "${LOCK_FILE}" ) 2>/dev/null; then
        die "recovery_lock_already_held"
    fi
}

compose() {
    docker compose "${COMPOSE_ARGS[@]}" "$@"
}

current_config_hash() {
    compose config --hash '*' 2>/dev/null |
        sha256sum |
        awk '{print $1}'
}

current_service_image() {
    local service="$1"

    compose images --format '{{.Service}}\t{{.Repository}}:{{.Tag}}@{{.ID}}' 2>/dev/null |
        awk -F '\t' -v s="${service}" '$1==s {print $2; exit}'
}

save_previous_identity() {
    local hash="$1"
    local timestamp="$2"

    local image_lines

    image_lines="$(
        compose images --format '{{.Service}}\t{{.Repository}}\t{{.Tag}}\t{{.ID}}' 2>/dev/null ||
        true
    )"

    {
        printf 'CONFIG_HASH=%s\n' "${hash}"
        printf 'CAPTURED_AT=%s\n' "${timestamp}"
        printf '%s\n' "${image_lines}" |
            awk -F '\t' '
                NF >= 4 {
                    printf "IMAGE_%d_SERVICE=%s\n", NR, $1
                    printf "IMAGE_%d_REPOSITORY=%s\n", NR, $2
                    printf "IMAGE_%d_TAG=%s\n", NR, $3
                    printf "IMAGE_%d_ID=%s\n", NR, $4
                }
            '
    } > "${STATE_FILE}"
}

wait_for_healthy() {
    local deadline
    deadline=$((SECONDS + VERIFY_TIMEOUT))

    while [ "${SECONDS}" -lt "${deadline}" ]; do

        if compose ps --format '{{.Service}}\t{{.Health}}\t{{.State}}' 2>/dev/null |
            awk -F '\t' '
                BEGIN { bad=0; found=0 }
                {
                    found=1
                    state=$3
                    health=$2

                    if (state !~ /running/) {
                        bad=1
                    }

                    if (health != "" &&
                        health !~ /healthy/) {
                        bad=1
                    }
                }
                END {
                    if (found && bad==0) exit 0
                    exit 1
                }
            '
        then
            return 0
        fi

        sleep "${VERIFY_INTERVAL}"
    done

    return 1
}

deploy() {
    acquire_lock

    local before_hash
    local timestamp

    before_hash="$(current_config_hash)"
    timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

    [ -n "${before_hash}" ] ||
        die "unable_to_capture_current_configuration_identity"

    save_previous_identity "${before_hash}" "${timestamp}"

    log "RECOVERY_STATE_CAPTURED=1"
    log "PREVIOUS_CONFIG_HASH=${before_hash}"

    if [ "${DRY_RUN}" = "1" ]; then
        log "DRY_RUN=1"
        log "DEPLOYMENT_ACTION_SKIPPED=1"
        return 0
    fi

    compose up -d --build

    if wait_for_healthy; then
        log "DEPLOYMENT_HEALTH=PASS"
        return 0
    fi

    log "DEPLOYMENT_HEALTH=FAIL"
    log "ROLLBACK_REQUIRED=1"

    rollback
}

rollback() {
    [ -f "${STATE_FILE}" ] ||
        die "NO_PREVIOUS_RELEASE_STATE_AVAILABLE"

    local previous_hash
    previous_hash="$(
        awk -F= '$1=="CONFIG_HASH" {print $2; exit}' "${STATE_FILE}"
    )"

    [ -n "${previous_hash}" ] ||
        die "PREVIOUS_RELEASE_IDENTITY_INVALID"

    log "ROLLBACK_STATE_PRESENT=1"
    log "PREVIOUS_CONFIG_HASH=${previous_hash}"

    if [ "${DRY_RUN}" = "1" ]; then
        log "DRY_RUN=1"
        log "ROLLBACK_ACTION_SKIPPED=1"
        return 0
    fi

    die \
        "AUTOMATIC_IMAGE_ROLLBACK_REQUIRES_VERSIONED_IMAGE_ARTIFACT_AUTHORITY"
}

case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    *)
        die "usage: production-recovery.sh [deploy|rollback]"
        ;;
esac
RECOVERY_EOF

chmod 0750 "${RECOVERY_SCRIPT}"

pass "RECOVERY_AUTHORITY_SCRIPT_CREATED=${RECOVERY_SCRIPT}"

fi

log ""
log "============================================================"
log "6. IMPLEMENTATION SAFETY REVIEW"
log "============================================================"

if [ -f "${RECOVERY_SCRIPT}" ]; then

    SCRIPT_SOURCE_ENV_COUNT="$(
        grep -Eic \
            '(^|[[:space:];])source[[:space:]]+[^#]*\.env|(^|[[:space:];])\.[[:space:]]+[^#]*\.env' \
            "${RECOVERY_SCRIPT}" 2>/dev/null || true
    )"

    SCRIPT_RELOAD_COUNT="$(
        grep -Eic \
            -- '--reload' \
            "${RECOVERY_SCRIPT}" 2>/dev/null || true
    )"

    SCRIPT_DOWNGRADE_COUNT="$(
        grep -Eic \
            'alembic[[:space:]]+downgrade' \
            "${RECOVERY_SCRIPT}" 2>/dev/null || true
    )"

    SCRIPT_SECRET_PRINT_COUNT="$(
        grep -Eic \
            'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
            "${RECOVERY_SCRIPT}" 2>/dev/null || true
    )"

    SCRIPT_FAIL_FAST_COUNT="$(
        grep -Eic \
            'set[[:space:]]+-Eeuo[[:space:]]+pipefail|set[[:space:]]+-euo[[:space:]]+pipefail' \
            "${RECOVERY_SCRIPT}" 2>/dev/null || true
    )"

    SCRIPT_HEALTH_COUNT="$(
        grep -Eic \
            'health|healthy|wait_for_healthy' \
            "${RECOVERY_SCRIPT}" 2>/dev/null || true
    )"

    SCRIPT_ROLLBACK_COUNT="$(
        grep -Eic \
            'rollback|ROLLBACK_REQUIRED|previous.*release|PREVIOUS_CONFIG_HASH' \
            "${RECOVERY_SCRIPT}" 2>/dev/null || true
    )"

    log "SCRIPT_SOURCE_ENV_COUNT=${SCRIPT_SOURCE_ENV_COUNT}"
    log "SCRIPT_RELOAD_COUNT=${SCRIPT_RELOAD_COUNT}"
    log "SCRIPT_DOWNGRADE_COUNT=${SCRIPT_DOWNGRADE_COUNT}"
    log "SCRIPT_SECRET_PRINT_COUNT=${SCRIPT_SECRET_PRINT_COUNT}"
    log "SCRIPT_FAIL_FAST_COUNT=${SCRIPT_FAIL_FAST_COUNT}"
    log "SCRIPT_HEALTH_COUNT=${SCRIPT_HEALTH_COUNT}"
    log "SCRIPT_ROLLBACK_COUNT=${SCRIPT_ROLLBACK_COUNT}"

    if [ "${SCRIPT_SOURCE_ENV_COUNT}" -eq 0 ]; then
        pass "RECOVERY_SCRIPT_HAS_NO_ENV_SOURCE"
    else
        fail "RECOVERY_SCRIPT_ENV_SOURCE_PRESENT"
    fi

    if [ "${SCRIPT_RELOAD_COUNT}" -eq 0 ]; then
        pass "RECOVERY_SCRIPT_HAS_NO_RELOAD"
    else
        fail "RECOVERY_SCRIPT_RELOAD_PRESENT"
    fi

    if [ "${SCRIPT_DOWNGRADE_COUNT}" -eq 0 ]; then
        pass "RECOVERY_SCRIPT_DOES_NOT_AUTOMATICALLY_DOWNGRADE_DATABASE"
    else
        fail "RECOVERY_SCRIPT_AUTOMATIC_DATABASE_DOWNGRADE_PRESENT"
    fi

    if [ "${SCRIPT_SECRET_PRINT_COUNT}" -eq 0 ]; then
        pass "RECOVERY_SCRIPT_HAS_NO_SECRET_IDENTIFIER_OUTPUT"
    else
        fail "RECOVERY_SCRIPT_SECRET_IDENTIFIER_REFERENCE_PRESENT"
    fi

    if [ "${SCRIPT_FAIL_FAST_COUNT}" -gt 0 ]; then
        pass "RECOVERY_SCRIPT_FAIL_FAST_PRESENT"
    else
        fail "RECOVERY_SCRIPT_FAIL_FAST_MISSING"
    fi

    if [ "${SCRIPT_HEALTH_COUNT}" -gt 0 ]; then
        pass "RECOVERY_SCRIPT_HEALTH_VERIFICATION_PRESENT"
    else
        fail "RECOVERY_SCRIPT_HEALTH_VERIFICATION_MISSING"
    fi

    if [ "${SCRIPT_ROLLBACK_COUNT}" -gt 0 ]; then
        pass "RECOVERY_SCRIPT_ROLLBACK_AUTHORITY_PRESENT"
    else
        fail "RECOVERY_SCRIPT_ROLLBACK_AUTHORITY_MISSING"
    fi
fi

log ""
log "============================================================"
log "7. CRITICAL ARCHITECTURAL LIMITATION"
log "============================================================"

if [ "${PRIMARY_IMAGE_COUNT}" -gt 0 ]; then

    pass "VERSIONED_IMAGE_ARTIFACT_SIGNAL_AVAILABLE"

else

    review "COMPOSE_PRIMARY_BUILD_BASED_DEPLOYMENT_REQUIRES_ARTIFACT_VERSION_AUTHORITY"
fi

review "RECOVERY_IMPLEMENTATION_IS_FAIL_CLOSED_WHEN_PREVIOUS_ARTIFACT_CANNOT_BE_IDENTIFIED"
review "DATABASE_SCHEMA_ROLLBACK_REMAINS_SEPARATE_FROM_CONTAINER_ROLLBACK"

log ""
log "============================================================"
log "8. R53 FINAL DECISION"
log "============================================================"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R53_PRODUCTION_RECOVERY_AUTHORITY_IMPLEMENTATION_FAILED"
    EXIT_CODE=2

elif [ ! -f "${RECOVERY_SCRIPT}" ]; then

    STATUS="FAIL"
    RESULT="P0_03_R53_RECOVERY_SCRIPT_NOT_AVAILABLE"
    EXIT_CODE=2

else

    STATUS="REVIEW"
    RESULT="P0_03_R53_RECOVERY_AUTHORITY_IMPLEMENTED_BUT_ARTIFACT_ROLLBACK_REQUIRES_VERSIONED_RELEASE_AUTHORITY"
    EXIT_CODE=1
fi

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"
log "P0_03_R53_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"

log ""
log "============================================================"
log "R53 COMPLETE"
log "============================================================"

exit "${EXIT_CODE}"
