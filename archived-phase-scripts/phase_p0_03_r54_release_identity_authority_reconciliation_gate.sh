#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
IFS=$'\n\t'

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"

REPORT="${PROJECT_ROOT}/p0_03_r54_release_identity_authority_reconciliation_gate.txt"

DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"
RECOVERY_SCRIPT="${PROJECT_ROOT}/scripts/production-recovery.sh"
COMPOSE="${PROJECT_ROOT}/docker-compose.yml"
COMPOSE_PRODUCTION="${PROJECT_ROOT}/docker-compose.production.yml"
CI="${PROJECT_ROOT}/.github/workflows/ci.yml"

FAILURE_COUNT=0
REVIEW_COUNT=0

GIT_SHA_COUNT=0
GIT_REVISION_COUNT=0
GIT_COMMIT_COUNT=0
RELEASE_ID_COUNT=0
VERSION_COUNT=0
IMAGE_TAG_COUNT=0
IMAGE_DIGEST_COUNT=0
ARTIFACT_COUNT=0
REGISTRY_COUNT=0

CI_SHA_COUNT=0
CI_TAG_COUNT=0
CI_VERSION_COUNT=0
CI_ARTIFACT_COUNT=0
CI_REGISTRY_COUNT=0

DEPLOY_SHA_COUNT=0
DEPLOY_TAG_COUNT=0
DEPLOY_VERSION_COUNT=0
DEPLOY_ARTIFACT_COUNT=0
DEPLOY_REGISTRY_COUNT=0

COMPOSE_IMAGE_COUNT=0
COMPOSE_TAGGED_IMAGE_COUNT=0
COMPOSE_DIGEST_COUNT=0
COMPOSE_BUILD_COUNT=0

RECOVERY_RELEASE_ID_COUNT=0
RECOVERY_STATE_COUNT=0
RECOVERY_CONFIG_HASH_COUNT=0

RELEASE_IDENTITY_AUTHORITY=0
IMMUTABLE_RELEASE_AUTHORITY=0
ROLLBACK_IDENTITY_AUTHORITY=0
ARTIFACT_RELEASE_AUTHORITY=0
PRODUCTION_RELEASE_HANDOFF=0

log() {
    printf '%s\n' "$*" | tee -a "${REPORT}"
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

count_pattern() {
    local pattern="$1"
    local file="$2"

    if [ -f "${file}" ]; then
        grep -Eic "${pattern}" "${file}" 2>/dev/null || true
    else
        printf '0\n'
    fi
}

: > "${REPORT}"

log "============================================================"
log "P0-03 R54 RELEASE IDENTITY AUTHORITY RECONCILIATION GATE"
log "============================================================"
log ""

log "============================================================"
log "1. SAFETY CONTRACT"
log "============================================================"

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "NO_SECRET_VALUES_READ=YES"
pass "NO_DATABASE_MODIFICATION=YES"
pass "NO_GIT_COMMAND_EXECUTION=YES"
pass "FAIL_CLOSED=YES"
pass "RELEASE_IDENTITY_SCOPE_ONLY=YES"

log ""
log "============================================================"
log "2. AUTHORITY FILE PRESENCE"
log "============================================================"

for pair in \
    "${DEPLOY_SCRIPT}|PRIMARY_DEPLOY_SCRIPT" \
    "${RECOVERY_SCRIPT}|RECOVERY_SCRIPT" \
    "${COMPOSE}|PRIMARY_COMPOSE" \
    "${CI}|CI_WORKFLOW"
do
    file="${pair%%|*}"
    name="${pair##*|}"

    if [ -f "${file}" ]; then
        pass "${name}_PRESENT"
    else
        review "${name}_NOT_PRESENT"
    fi
done

log ""
log "============================================================"
log "3. REPOSITORY RELEASE IDENTITY SIGNALS"
log "============================================================"

SEARCH_ROOTS=(
    "${DEPLOY_SCRIPT}"
    "${RECOVERY_SCRIPT}"
    "${COMPOSE}"
    "${COMPOSE_PRODUCTION}"
    "${CI}"
)

GIT_SHA_PATTERN='GIT_SHA|GIT_COMMIT_SHA|COMMIT_SHA|COMMIT_HASH|GITHUB_SHA|CI_COMMIT_SHA|SOURCE_COMMIT'
GIT_REVISION_PATTERN='GIT_REVISION|REVISION|SOURCE_REVISION|BUILD_REVISION'
GIT_COMMIT_PATTERN='GIT_COMMIT|COMMIT_ID|COMMIT_HASH'
RELEASE_ID_PATTERN='RELEASE_ID|RELEASE_VERSION|RELEASE_TAG|RELEASE_NAME'
VERSION_PATTERN='APP_VERSION|BUILD_VERSION|RELEASE_VERSION|VERSION='
IMAGE_TAG_PATTERN='IMAGE_TAG|IMAGE_VERSION|IMAGE_NAME|TAG='
IMAGE_DIGEST_PATTERN='@sha256:[0-9a-fA-F]{64}'
ARTIFACT_PATTERN='artifact|image[[:space:]_-]*artifact|release[[:space:]_-]*artifact'
REGISTRY_PATTERN='registry|ghcr\.io|docker\.io|ecr|gcr\.io|artifactregistry'

for file in "${SEARCH_ROOTS[@]}"; do
    [ -f "${file}" ] || continue

    GIT_SHA_COUNT=$((GIT_SHA_COUNT + $(count_pattern "${GIT_SHA_PATTERN}" "${file}")))
    GIT_REVISION_COUNT=$((GIT_REVISION_COUNT + $(count_pattern "${GIT_REVISION_PATTERN}" "${file}")))
    GIT_COMMIT_COUNT=$((GIT_COMMIT_COUNT + $(count_pattern "${GIT_COMMIT_PATTERN}" "${file}")))
    RELEASE_ID_COUNT=$((RELEASE_ID_COUNT + $(count_pattern "${RELEASE_ID_PATTERN}" "${file}")))
    VERSION_COUNT=$((VERSION_COUNT + $(count_pattern "${VERSION_PATTERN}" "${file}")))
    IMAGE_TAG_COUNT=$((IMAGE_TAG_COUNT + $(count_pattern "${IMAGE_TAG_PATTERN}" "${file}")))
    IMAGE_DIGEST_COUNT=$((IMAGE_DIGEST_COUNT + $(count_pattern "${IMAGE_DIGEST_PATTERN}" "${file}")))
    ARTIFACT_COUNT=$((ARTIFACT_COUNT + $(count_pattern "${ARTIFACT_PATTERN}" "${file}")))
    REGISTRY_COUNT=$((REGISTRY_COUNT + $(count_pattern "${REGISTRY_PATTERN}" "${file}")))
done

log "GIT_SHA_COUNT=${GIT_SHA_COUNT}"
log "GIT_REVISION_COUNT=${GIT_REVISION_COUNT}"
log "GIT_COMMIT_COUNT=${GIT_COMMIT_COUNT}"
log "RELEASE_ID_COUNT=${RELEASE_ID_COUNT}"
log "VERSION_COUNT=${VERSION_COUNT}"
log "IMAGE_TAG_COUNT=${IMAGE_TAG_COUNT}"
log "IMAGE_DIGEST_COUNT=${IMAGE_DIGEST_COUNT}"
log "ARTIFACT_COUNT=${ARTIFACT_COUNT}"
log "REGISTRY_COUNT=${REGISTRY_COUNT}"

if [ "${GIT_SHA_COUNT}" -gt 0 ] ||
   [ "${GIT_REVISION_COUNT}" -gt 0 ] ||
   [ "${GIT_COMMIT_COUNT}" -gt 0 ]; then
    pass "SOURCE_REVISION_IDENTITY_SIGNAL_PRESENT"
else
    review "SOURCE_REVISION_IDENTITY_SIGNAL_NOT_DETECTED"
fi

if [ "${RELEASE_ID_COUNT}" -gt 0 ] ||
   [ "${VERSION_COUNT}" -gt 0 ] ||
   [ "${IMAGE_TAG_COUNT}" -gt 0 ]; then
    pass "RELEASE_VERSION_IDENTITY_SIGNAL_PRESENT"
else
    review "RELEASE_VERSION_IDENTITY_SIGNAL_NOT_DETECTED"
fi

if [ "${IMAGE_DIGEST_COUNT}" -gt 0 ]; then
    IMMUTABLE_RELEASE_AUTHORITY=1
    pass "IMMUTABLE_IMAGE_DIGEST_SIGNAL_PRESENT"
else
    review "IMMUTABLE_IMAGE_DIGEST_NOT_DETECTED"
fi

if [ "${ARTIFACT_COUNT}" -gt 0 ] &&
   [ "${REGISTRY_COUNT}" -gt 0 ]; then
    ARTIFACT_RELEASE_AUTHORITY=1
    pass "ARTIFACT_REGISTRY_RELEASE_SIGNAL_PRESENT"
else
    review "ARTIFACT_REGISTRY_RELEASE_AUTHORITY_NOT_ESTABLISHED"
fi

log ""
log "============================================================"
log "4. CI RELEASE IDENTITY HANDOFF"
log "============================================================"

if [ -f "${CI}" ]; then

    CI_SHA_COUNT="$(
        count_pattern \
            'GITHUB_SHA|CI_COMMIT_SHA|COMMIT_SHA|GIT_SHA|GIT_COMMIT' \
            "${CI}"
    )"

    CI_TAG_COUNT="$(
        count_pattern \
            'IMAGE_TAG|IMAGE_VERSION|RELEASE_TAG|GITHUB_REF|GITHUB_REF_NAME' \
            "${CI}"
    )"

    CI_VERSION_COUNT="$(
        count_pattern \
            'VERSION=|APP_VERSION|BUILD_VERSION|RELEASE_VERSION' \
            "${CI}"
    )"

    CI_ARTIFACT_COUNT="$(
        count_pattern \
            'artifact|upload-artifact|download-artifact|release' \
            "${CI}"
    )"

    CI_REGISTRY_COUNT="$(
        count_pattern \
            'registry|ghcr\.io|docker\.io|ecr|gcr\.io|artifactregistry' \
            "${CI}"
    )"
fi

log "CI_SHA_COUNT=${CI_SHA_COUNT}"
log "CI_TAG_COUNT=${CI_TAG_COUNT}"
log "CI_VERSION_COUNT=${CI_VERSION_COUNT}"
log "CI_ARTIFACT_COUNT=${CI_ARTIFACT_COUNT}"
log "CI_REGISTRY_COUNT=${CI_REGISTRY_COUNT}"

if [ "${CI_SHA_COUNT}" -gt 0 ]; then
    pass "CI_SOURCE_REVISION_SIGNAL_PRESENT"
else
    review "CI_SOURCE_REVISION_SIGNAL_NOT_DETECTED"
fi

if [ "${CI_TAG_COUNT}" -gt 0 ] ||
   [ "${CI_VERSION_COUNT}" -gt 0 ]; then
    pass "CI_RELEASE_IDENTITY_SIGNAL_PRESENT"
else
    review "CI_RELEASE_IDENTITY_SIGNAL_NOT_DETECTED"
fi

if [ "${CI_ARTIFACT_COUNT}" -gt 0 ] &&
   [ "${CI_REGISTRY_COUNT}" -gt 0 ]; then
    pass "CI_ARTIFACT_RELEASE_HANDOFF_SIGNAL_PRESENT"
else
    review "CI_ARTIFACT_RELEASE_HANDOFF_NOT_ESTABLISHED"
fi

log ""
log "============================================================"
log "5. PRIMARY DEPLOYMENT RELEASE IDENTITY"
log "============================================================"

if [ -f "${DEPLOY_SCRIPT}" ]; then

    DEPLOY_SHA_COUNT="$(
        count_pattern \
            'GITHUB_SHA|CI_COMMIT_SHA|COMMIT_SHA|GIT_SHA|GIT_COMMIT|REVISION' \
            "${DEPLOY_SCRIPT}"
    )"

    DEPLOY_TAG_COUNT="$(
        count_pattern \
            'IMAGE_TAG|IMAGE_VERSION|RELEASE_TAG|TAG=' \
            "${DEPLOY_SCRIPT}"
    )"

    DEPLOY_VERSION_COUNT="$(
        count_pattern \
            'VERSION=|APP_VERSION|BUILD_VERSION|RELEASE_VERSION' \
            "${DEPLOY_SCRIPT}"
    )"

    DEPLOY_ARTIFACT_COUNT="$(
        count_pattern \
            'artifact|release[[:space:]_-]*artifact|image[[:space:]_-]*artifact' \
            "${DEPLOY_SCRIPT}"
    )"

    DEPLOY_REGISTRY_COUNT="$(
        count_pattern \
            'registry|ghcr\.io|docker\.io|ecr|gcr\.io|artifactregistry' \
            "${DEPLOY_SCRIPT}"
    )"
fi

log "DEPLOY_SHA_COUNT=${DEPLOY_SHA_COUNT}"
log "DEPLOY_TAG_COUNT=${DEPLOY_TAG_COUNT}"
log "DEPLOY_VERSION_COUNT=${DEPLOY_VERSION_COUNT}"
log "DEPLOY_ARTIFACT_COUNT=${DEPLOY_ARTIFACT_COUNT}"
log "DEPLOY_REGISTRY_COUNT=${DEPLOY_REGISTRY_COUNT}"

if [ "${DEPLOY_SHA_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_TAG_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_VERSION_COUNT}" -gt 0 ]; then
    pass "DEPLOYMENT_RELEASE_IDENTITY_SIGNAL_PRESENT"
else
    review "DEPLOYMENT_RELEASE_IDENTITY_NOT_EXPLICITLY_PRESENT"
fi

if [ "${DEPLOY_ARTIFACT_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_REGISTRY_COUNT}" -gt 0 ]; then
    pass "DEPLOYMENT_ARTIFACT_SOURCE_SIGNAL_PRESENT"
else
    review "DEPLOYMENT_ARTIFACT_SOURCE_NOT_EXPLICITLY_PRESENT"
fi

log ""
log "============================================================"
log "6. COMPOSE IMAGE IDENTITY"
log "============================================================"

if [ -f "${COMPOSE}" ]; then

    COMPOSE_IMAGE_COUNT="$(
        grep -Eic \
            '^[[:space:]]*image:[[:space:]]*[^[:space:]]+' \
            "${COMPOSE}" 2>/dev/null || true
    )"

    COMPOSE_TAGGED_IMAGE_COUNT="$(
        grep -Eic \
            '^[[:space:]]*image:[[:space:]]*[^[:space:]]+:[^[:space:]]+' \
            "${COMPOSE}" 2>/dev/null || true
    )"

    COMPOSE_DIGEST_COUNT="$(
        count_pattern \
            '@sha256:[0-9a-fA-F]{64}' \
            "${COMPOSE}"
    )"

    COMPOSE_BUILD_COUNT="$(
        grep -Eic \
            '^[[:space:]]*build:' \
            "${COMPOSE}" 2>/dev/null || true
    )"
fi

log "COMPOSE_IMAGE_COUNT=${COMPOSE_IMAGE_COUNT}"
log "COMPOSE_TAGGED_IMAGE_COUNT=${COMPOSE_TAGGED_IMAGE_COUNT}"
log "COMPOSE_DIGEST_COUNT=${COMPOSE_DIGEST_COUNT}"
log "COMPOSE_BUILD_COUNT=${COMPOSE_BUILD_COUNT}"

if [ "${COMPOSE_IMAGE_COUNT}" -gt 0 ]; then
    pass "COMPOSE_IMAGE_IDENTITY_PRESENT"
else
    review "COMPOSE_IMAGE_IDENTITY_NOT_PRESENT"
fi

if [ "${COMPOSE_TAGGED_IMAGE_COUNT}" -gt 0 ]; then
    pass "COMPOSE_TAGGED_IMAGE_IDENTITY_PRESENT"
else
    review "COMPOSE_TAGGED_IMAGE_IDENTITY_NOT_PRESENT"
fi

if [ "${COMPOSE_DIGEST_COUNT}" -gt 0 ]; then
    IMMUTABLE_RELEASE_AUTHORITY=1
    pass "COMPOSE_IMMUTABLE_DIGEST_PRESENT"
else
    review "COMPOSE_IMMUTABLE_DIGEST_NOT_PRESENT"
fi

log ""
log "============================================================"
log "7. RECOVERY STATE IDENTITY"
log "============================================================"

if [ -f "${RECOVERY_SCRIPT}" ]; then

    RECOVERY_RELEASE_ID_COUNT="$(
        count_pattern \
            'RELEASE_ID|RELEASE_VERSION|IMAGE_TAG|IMAGE_ID|PREVIOUS.*RELEASE|PREVIOUS.*IMAGE' \
            "${RECOVERY_SCRIPT}"
    )"

    RECOVERY_STATE_COUNT="$(
        count_pattern \
            'STATE_FILE|previous-release|PREVIOUS_CONFIG_HASH' \
            "${RECOVERY_SCRIPT}"
    )"

    RECOVERY_CONFIG_HASH_COUNT="$(
        count_pattern \
            'CONFIG_HASH|current_config_hash' \
            "${RECOVERY_SCRIPT}"
    )"
fi

log "RECOVERY_RELEASE_ID_COUNT=${RECOVERY_RELEASE_ID_COUNT}"
log "RECOVERY_STATE_COUNT=${RECOVERY_STATE_COUNT}"
log "RECOVERY_CONFIG_HASH_COUNT=${RECOVERY_CONFIG_HASH_COUNT}"

if [ "${RECOVERY_STATE_COUNT}" -gt 0 ]; then
    pass "RECOVERY_STATE_AUTHORITY_PRESENT"
else
    review "RECOVERY_STATE_AUTHORITY_NOT_PRESENT"
fi

if [ "${RECOVERY_CONFIG_HASH_COUNT}" -gt 0 ]; then
    pass "RECOVERY_CONFIGURATION_IDENTITY_PRESENT"
else
    review "RECOVERY_CONFIGURATION_IDENTITY_NOT_PRESENT"
fi

if [ "${RECOVERY_RELEASE_ID_COUNT}" -gt 0 ]; then
    pass "RECOVERY_RELEASE_IDENTITY_REFERENCE_PRESENT"
else
    review "RECOVERY_RELEASE_IDENTITY_REFERENCE_NOT_EXPLICIT"
fi

log ""
log "============================================================"
log "8. RELEASE IDENTITY CLASSIFICATION"
log "============================================================"

RELEASE_IDENTITY_AUTHORITY=0
ROLLBACK_IDENTITY_AUTHORITY=0
PRODUCTION_RELEASE_HANDOFF=0

if [ "${GIT_SHA_COUNT}" -gt 0 ] &&
   [ "${CI_SHA_COUNT}" -gt 0 ] &&
   { [ "${DEPLOY_SHA_COUNT}" -gt 0 ] || [ "${DEPLOY_TAG_COUNT}" -gt 0 ] || [ "${DEPLOY_VERSION_COUNT}" -gt 0 ]; }; then

    RELEASE_IDENTITY_AUTHORITY=1
    PRODUCTION_RELEASE_HANDOFF=1
    pass "SOURCE_TO_PRODUCTION_RELEASE_IDENTITY_CHAIN_PRESENT"

else

    review "SOURCE_TO_PRODUCTION_RELEASE_IDENTITY_CHAIN_INCOMPLETE"
fi

if [ "${IMMUTABLE_RELEASE_AUTHORITY}" -eq 1 ]; then
    pass "IMMUTABLE_RELEASE_AUTHORITY_PRESENT"
else
    review "IMMUTABLE_RELEASE_AUTHORITY_NOT_ESTABLISHED"
fi

if [ "${RECOVERY_STATE_COUNT}" -gt 0 ] &&
   { [ "${COMPOSE_TAGGED_IMAGE_COUNT}" -gt 0 ] || [ "${COMPOSE_DIGEST_COUNT}" -gt 0 ]; }; then

    ROLLBACK_IDENTITY_AUTHORITY=1
    pass "RECOVERY_CAN_REFERENCE_VERSIONED_RELEASE_IDENTITY"

else

    review "RECOVERY_CANNOT_YET_PROVE_VERSIONED_RELEASE_ROLLBACK_IDENTITY"
fi

log "RELEASE_IDENTITY_AUTHORITY=${RELEASE_IDENTITY_AUTHORITY}"
log "IMMUTABLE_RELEASE_AUTHORITY=${IMMUTABLE_RELEASE_AUTHORITY}"
log "ROLLBACK_IDENTITY_AUTHORITY=${ROLLBACK_IDENTITY_AUTHORITY}"
log "ARTIFACT_RELEASE_AUTHORITY=${ARTIFACT_RELEASE_AUTHORITY}"
log "PRODUCTION_RELEASE_HANDOFF=${PRODUCTION_RELEASE_HANDOFF}"

log ""
log "============================================================"
log "9. R53 HANDOFF"
log "============================================================"

if [ -f "${RECOVERY_SCRIPT}" ]; then
    pass "R53_RECOVERY_IMPLEMENTATION_PRESENT"
else
    fail "R53_RECOVERY_IMPLEMENTATION_MISSING"
fi

if [ "${RECOVERY_STATE_COUNT}" -gt 0 ]; then
    pass "R53_STATE_CAPTURE_MECHANISM_PRESENT"
else
    fail "R53_STATE_CAPTURE_MECHANISM_MISSING"
fi

log ""
log "============================================================"
log "10. FINAL R54 DECISION"
log "============================================================"

log "RELEASE_IDENTITY_AUTHORITY=${RELEASE_IDENTITY_AUTHORITY}"
log "IMMUTABLE_RELEASE_AUTHORITY=${IMMUTABLE_RELEASE_AUTHORITY}"
log "ROLLBACK_IDENTITY_AUTHORITY=${ROLLBACK_IDENTITY_AUTHORITY}"
log "ARTIFACT_RELEASE_AUTHORITY=${ARTIFACT_RELEASE_AUTHORITY}"
log "PRODUCTION_RELEASE_HANDOFF=${PRODUCTION_RELEASE_HANDOFF}"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R54_RELEASE_IDENTITY_AUTHORITY_GATE_FAILED"
    EXIT_CODE=2

elif [ "${ROLLBACK_IDENTITY_AUTHORITY}" -eq 1 ] &&
     [ "${RELEASE_IDENTITY_AUTHORITY}" -eq 1 ]; then

    STATUS="PASS"
    RESULT="P0_03_R54_RELEASE_IDENTITY_AUTHORITY_ESTABLISHED"
    EXIT_CODE=0

else

    STATUS="REVIEW"
    RESULT="P0_03_R54_RELEASE_IDENTITY_AUTHORITY_REQUIRES_IMPLEMENTATION"
    EXIT_CODE=1
fi

log "P0_03_R54_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"

log ""
log "============================================================"
log "R54 COMPLETE"
log "============================================================"

exit "${EXIT_CODE}"
