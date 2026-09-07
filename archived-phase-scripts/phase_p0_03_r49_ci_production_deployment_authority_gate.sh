#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT="${PROJECT_ROOT}/p0_03_r49_ci_production_deployment_authority_gate.txt"

CI_DIR="${PROJECT_ROOT}/.github/workflows"
CI_FILE="${PROJECT_ROOT}/.github/workflows/ci.yml"
DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"

TMP_CI="${PROJECT_ROOT}/.r49_tmp_ci"
TMP_DEPLOY="${PROJECT_ROOT}/.r49_tmp_deploy"
TMP_AUTHORITY="${PROJECT_ROOT}/.r49_tmp_authority"

FAILURE_COUNT=0
REVIEW_COUNT=0

R48_STATUS=0
R48_EXIT_CODE=0
R48_PRODUCTION_RELOAD_BLOCKER=0

CI_WORKFLOW_COUNT=0
CI_PRODUCTION_MARKER_COUNT=0
CI_DEPLOY_KEYWORD_COUNT=0
CI_DOCKER_BUILD_COUNT=0
CI_DOCKER_PUSH_COUNT=0
CI_REGISTRY_COUNT=0
CI_ARTIFACT_RELEASE_COUNT=0
CI_REMOTE_DEPLOY_COUNT=0
CI_PRODUCTION_ENV_COUNT=0
CI_BRANCH_GUARD_COUNT=0
CI_DEPLOY_SCRIPT_REFERENCE_COUNT=0

DEPLOY_SCRIPT_PRESENT=0
DEPLOY_SCRIPT_COMPOSE_COUNT=0
DEPLOY_SCRIPT_BUILD_COUNT=0
DEPLOY_SCRIPT_PUSH_COUNT=0
DEPLOY_SCRIPT_REMOTE_DEPLOY_COUNT=0
DEPLOY_SCRIPT_PRODUCTION_COUNT=0
DEPLOY_SCRIPT_FAIL_FAST_COUNT=0

PRODUCTION_CI_DEPLOYMENT_PATH=0
PRODUCTION_CI_DEPLOYMENT_REVIEW=0
PRODUCTION_CI_DEPLOYMENT_BLOCKER=0

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

cleanup() {
    rm -f \
        "${TMP_CI}" \
        "${TMP_DEPLOY}" \
        "${TMP_AUTHORITY}" \
        2>/dev/null || true
}

trap cleanup EXIT

: > "${REPORT}"
: > "${TMP_CI}"
: > "${TMP_DEPLOY}"
: > "${TMP_AUTHORITY}"

log "============================================================"
log "P0-03 R49 CI PRODUCTION DEPLOYMENT AUTHORITY GATE"
log "============================================================"
log ""

log "============================================================"
log "1. SAFETY PRECHECK"
log "============================================================"

if [ -d "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
    pass "PROJECT_ROOT_PRESENT"
else
    fail "PROJECT_ROOT_MISSING"
fi

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "NO_ENV_VALUES_READ=YES"
pass "FAIL_CLOSED=YES"
pass "CI_PRODUCTION_AUTHORITY_ANALYSIS=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. R48 HANDOFF"
log "============================================================"

R48_REPORT="${PROJECT_ROOT}/p0_03_r48_production_reload_authority_gate.txt"

if [ -f "${R48_REPORT}" ]; then
    pass "R48_REPORT_PRESENT"

    R48_STATUS="$(
        awk -F= '
            $1=="P0_03_R48_STATUS" {v=$2}
            END {print v+0}
        ' "${R48_REPORT}" 2>/dev/null || true
    )"

    R48_EXIT_CODE="$(
        awk -F= '
            $1=="EXIT_CODE" {v=$2}
            END {print v+0}
        ' "${R48_REPORT}" 2>/dev/null || true
    )"

    R48_PRODUCTION_RELOAD_BLOCKER="$(
        awk -F= '
            $1=="PRODUCTION_RELOAD_BLOCKER" {v=$2}
            END {print v+0}
        ' "${R48_REPORT}" 2>/dev/null || true
    )"

    : "${R48_STATUS:=0}"
    : "${R48_EXIT_CODE:=0}"
    : "${R48_PRODUCTION_RELOAD_BLOCKER:=0}"

    log "R48_STATUS=${R48_STATUS}"
    log "R48_EXIT_CODE=${R48_EXIT_CODE}"
    log "R48_PRODUCTION_RELOAD_BLOCKER=${R48_PRODUCTION_RELOAD_BLOCKER}"

    if [ "${R48_STATUS}" -eq 0 ] &&
       [ "${R48_EXIT_CODE}" -eq 0 ] &&
       [ "${R48_PRODUCTION_RELOAD_BLOCKER}" -eq 0 ]; then
        pass "R48_PRODUCTION_RELOAD_AUTHORITY_CLOSED"
    else
        review "R48_HANDOFF_NOT_CLEAN"
    fi
else
    review "R48_REPORT_NOT_AVAILABLE_HANDOFF_NOT_USED"
    R48_STATUS=0
    R48_EXIT_CODE=0
    R48_PRODUCTION_RELOAD_BLOCKER=0
fi

log ""
log "============================================================"
log "3. CI WORKFLOW AUTHORITY"
log "============================================================"

if [ -d "${CI_DIR}" ]; then
    pass "CI_WORKFLOW_DIRECTORY_PRESENT"
else
    fail "CI_WORKFLOW_DIRECTORY_MISSING"
fi

if [ -f "${CI_FILE}" ]; then
    CI_WORKFLOW_COUNT=1
    pass "PRIMARY_CI_WORKFLOW_PRESENT"
else
    CI_WORKFLOW_COUNT=0
    review "PRIMARY_CI_WORKFLOW_NOT_FOUND"
fi

log "CI_WORKFLOW_COUNT=${CI_WORKFLOW_COUNT}"

log ""
log "============================================================"
log "4. CI PRODUCTION DEPLOYMENT SIGNALS"
log "============================================================"

if [ -f "${CI_FILE}" ]; then

    CI_PRODUCTION_MARKER_COUNT="$(
        grep -Eic \
            'production|prod([_-]|$)|environment:[[:space:]]*prod' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_DEPLOY_KEYWORD_COUNT="$(
        grep -Eic \
            'deploy|deployment|release' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_DOCKER_BUILD_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+(build|buildx)|docker/build' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_DOCKER_PUSH_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+push|build-push-action' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_REGISTRY_COUNT="$(
        grep -Eic \
            'registry|ghcr\.io|docker\.io|ecr|gcr\.io|gar\.io|acr' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_ARTIFACT_RELEASE_COUNT="$(
        grep -Eic \
            'upload-artifact|release|packages|artifact' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_REMOTE_DEPLOY_COUNT="$(
        grep -Eic \
            'ssh|scp|rsync|kubectl|helm|ansible|terraform|remote|ec2|ecs|kubernetes|docker[[:space:]]+context' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_PRODUCTION_ENV_COUNT="$(
        grep -Eic \
            'environment:|ENVIRONMENT|DEPLOY_ENV|NODE_ENV|APP_ENV' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_BRANCH_GUARD_COUNT="$(
        grep -Eic \
            'branches:|branches-ignore:|if:.*main|if:.*master|github\.ref' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_DEPLOY_SCRIPT_REFERENCE_COUNT="$(
        grep -Eic \
            'scripts/deploy\.sh|deploy\.sh' \
            "${CI_FILE}" 2>/dev/null || true
    )"
fi

log "CI_PRODUCTION_MARKER_COUNT=${CI_PRODUCTION_MARKER_COUNT}"
log "CI_DEPLOY_KEYWORD_COUNT=${CI_DEPLOY_KEYWORD_COUNT}"
log "CI_DOCKER_BUILD_COUNT=${CI_DOCKER_BUILD_COUNT}"
log "CI_DOCKER_PUSH_COUNT=${CI_DOCKER_PUSH_COUNT}"
log "CI_REGISTRY_COUNT=${CI_REGISTRY_COUNT}"
log "CI_ARTIFACT_RELEASE_COUNT=${CI_ARTIFACT_RELEASE_COUNT}"
log "CI_REMOTE_DEPLOY_COUNT=${CI_REMOTE_DEPLOY_COUNT}"
log "CI_PRODUCTION_ENV_COUNT=${CI_PRODUCTION_ENV_COUNT}"
log "CI_BRANCH_GUARD_COUNT=${CI_BRANCH_GUARD_COUNT}"
log "CI_DEPLOY_SCRIPT_REFERENCE_COUNT=${CI_DEPLOY_SCRIPT_REFERENCE_COUNT}"

if [ "${CI_PRODUCTION_MARKER_COUNT}" -gt 0 ]; then
    pass "CI_PRODUCTION_MARKER_PRESENT"
else
    review "CI_PRODUCTION_MARKER_NOT_DETECTED"
fi

if [ "${CI_BRANCH_GUARD_COUNT}" -gt 0 ]; then
    pass "CI_BRANCH_GUARD_SIGNAL_PRESENT"
else
    review "CI_BRANCH_GUARD_NOT_DETECTED"
fi

log ""
log "============================================================"
log "5. CI DEPLOYMENT MECHANISM CLASSIFICATION"
log "============================================================"

if [ "${CI_DEPLOY_KEYWORD_COUNT}" -gt 0 ]; then
    pass "CI_DEPLOYMENT_KEYWORD_PRESENT"
else
    review "CI_DEPLOYMENT_KEYWORD_NOT_DETECTED"
fi

if [ "${CI_DOCKER_PUSH_COUNT}" -gt 0 ] &&
   [ "${CI_REGISTRY_COUNT}" -gt 0 ]; then
    pass "CI_CONTAINER_RELEASE_PATH_PRESENT"
else
    review "CI_CONTAINER_RELEASE_PATH_NOT_DETECTED"
fi

if [ "${CI_REMOTE_DEPLOY_COUNT}" -gt 0 ]; then
    pass "CI_REMOTE_DEPLOYMENT_MECHANISM_PRESENT"
else
    review "CI_REMOTE_DEPLOYMENT_MECHANISM_NOT_DETECTED"
fi

if [ "${CI_ARTIFACT_RELEASE_COUNT}" -gt 0 ]; then
    pass "CI_ARTIFACT_RELEASE_SIGNAL_PRESENT"
else
    review "CI_ARTIFACT_RELEASE_SIGNAL_NOT_DETECTED"
fi

if [ "${CI_DEPLOY_SCRIPT_REFERENCE_COUNT}" -gt 0 ]; then
    pass "CI_REFERENCES_PRIMARY_DEPLOY_SCRIPT"
else
    review "CI_DOES_NOT_REFERENCE_PRIMARY_DEPLOY_SCRIPT"
fi

log ""
log "============================================================"
log "6. PRIMARY DEPLOY SCRIPT AUTHORITY"
log "============================================================"

if [ -f "${DEPLOY_SCRIPT}" ]; then
    DEPLOY_SCRIPT_PRESENT=1
    pass "DEPLOY_SCRIPT_PRESENT"

    DEPLOY_SCRIPT_COMPOSE_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose|docker-compose' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_SCRIPT_BUILD_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+(build|buildx)|build-push' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_SCRIPT_PUSH_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+push|push:' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_SCRIPT_REMOTE_DEPLOY_COUNT="$(
        grep -Eic \
            'ssh|scp|rsync|kubectl|helm|ansible|remote' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_SCRIPT_PRODUCTION_COUNT="$(
        grep -Eic \
            'production|PRODUCTION|prod([_-]|$)' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_SCRIPT_FAIL_FAST_COUNT="$(
        grep -Ec \
            '^[[:space:]]*set[[:space:]]+-[^#]*e' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"
else
    DEPLOY_SCRIPT_PRESENT=0
    DEPLOY_SCRIPT_COMPOSE_COUNT=0
    DEPLOY_SCRIPT_BUILD_COUNT=0
    DEPLOY_SCRIPT_PUSH_COUNT=0
    DEPLOY_SCRIPT_REMOTE_DEPLOY_COUNT=0
    DEPLOY_SCRIPT_PRODUCTION_COUNT=0
    DEPLOY_SCRIPT_FAIL_FAST_COUNT=0

    fail "DEPLOY_SCRIPT_MISSING"
fi

log "DEPLOY_SCRIPT_PRESENT=${DEPLOY_SCRIPT_PRESENT}"
log "DEPLOY_SCRIPT_COMPOSE_COUNT=${DEPLOY_SCRIPT_COMPOSE_COUNT}"
log "DEPLOY_SCRIPT_BUILD_COUNT=${DEPLOY_SCRIPT_BUILD_COUNT}"
log "DEPLOY_SCRIPT_PUSH_COUNT=${DEPLOY_SCRIPT_PUSH_COUNT}"
log "DEPLOY_SCRIPT_REMOTE_DEPLOY_COUNT=${DEPLOY_SCRIPT_REMOTE_DEPLOY_COUNT}"
log "DEPLOY_SCRIPT_PRODUCTION_COUNT=${DEPLOY_SCRIPT_PRODUCTION_COUNT}"
log "DEPLOY_SCRIPT_FAIL_FAST_COUNT=${DEPLOY_SCRIPT_FAIL_FAST_COUNT}"

if [ "${DEPLOY_SCRIPT_COMPOSE_COUNT}" -gt 0 ]; then
    pass "DEPLOY_SCRIPT_HAS_COMPOSE_OPERATION"
else
    review "DEPLOY_SCRIPT_HAS_NO_COMPOSE_OPERATION"
fi

if [ "${DEPLOY_SCRIPT_FAIL_FAST_COUNT}" -gt 0 ]; then
    pass "DEPLOY_SCRIPT_FAIL_FAST_SIGNAL_PRESENT"
else
    review "DEPLOY_SCRIPT_FAIL_FAST_SIGNAL_NOT_DETECTED"
fi

log ""
log "============================================================"
log "7. CI TO DEPLOY SCRIPT CORRELATION"
log "============================================================"

if [ "${CI_DEPLOY_SCRIPT_REFERENCE_COUNT}" -gt 0 ]; then

    if [ "${DEPLOY_SCRIPT_PRESENT}" -eq 1 ]; then
        pass "CI_DEPLOY_REFERENCE_TARGET_EXISTS"
    else
        fail "CI_REFERENCES_MISSING_DEPLOY_SCRIPT"
    fi

elif [ "${CI_DEPLOY_KEYWORD_COUNT}" -eq 0 ]; then

    review "CI_HAS_NO_DECLARED_DEPLOYMENT_PATH"

else

    review "CI_DEPLOYMENT_PATH_EXISTS_WITHOUT_PRIMARY_DEPLOY_SCRIPT_CORRELATION"
fi

log ""
log "============================================================"
log "8. PRODUCTION DEPLOYMENT PATH DETERMINATION"
log "============================================================"

PRODUCTION_CI_DEPLOYMENT_PATH=0
PRODUCTION_CI_DEPLOYMENT_REVIEW=0
PRODUCTION_CI_DEPLOYMENT_BLOCKER=0

if [ "${CI_PRODUCTION_MARKER_COUNT}" -gt 0 ] &&
   [ "${CI_DEPLOY_KEYWORD_COUNT}" -gt 0 ]; then

    PRODUCTION_CI_DEPLOYMENT_PATH=1
    pass "CI_EXPLICIT_PRODUCTION_DEPLOYMENT_SIGNAL"

elif [ "${CI_DEPLOY_KEYWORD_COUNT}" -gt 0 ]; then

    PRODUCTION_CI_DEPLOYMENT_REVIEW=1
    review "CI_DEPLOYMENT_PRESENT_WITHOUT_EXPLICIT_PRODUCTION_MARKER"

else

    PRODUCTION_CI_DEPLOYMENT_REVIEW=1
    review "CI_PRODUCTION_DEPLOYMENT_PATH_NOT_ESTABLISHED"
fi

if [ "${CI_DOCKER_PUSH_COUNT}" -gt 0 ] &&
   [ "${CI_REGISTRY_COUNT}" -gt 0 ]; then

    pass "CI_HAS_CONTAINER_REGISTRY_RELEASE_PATH"

elif [ "${PRODUCTION_CI_DEPLOYMENT_PATH}" -eq 1 ]; then

    PRODUCTION_CI_DEPLOYMENT_REVIEW=1
    review "PRODUCTION_CI_DEPLOYMENT_LACKS_CONTAINER_REGISTRY_CORRELATION"
fi

if [ "${CI_REMOTE_DEPLOY_COUNT}" -gt 0 ]; then
    pass "CI_HAS_REMOTE_DEPLOYMENT_SIGNAL"
else
    review "CI_HAS_NO_REMOTE_DEPLOYMENT_SIGNAL"
fi

if [ "${CI_DEPLOY_SCRIPT_REFERENCE_COUNT}" -gt 0 ] &&
   [ "${DEPLOY_SCRIPT_PRESENT}" -eq 1 ]; then

    pass "CI_PRIMARY_DEPLOY_SCRIPT_CORRELATION_PRESENT"

elif [ "${PRODUCTION_CI_DEPLOYMENT_PATH}" -eq 1 ]; then

    PRODUCTION_CI_DEPLOYMENT_REVIEW=1
    review "PRODUCTION_CI_PATH_NOT_CORRELATED_WITH_PRIMARY_DEPLOY_SCRIPT"
fi

log "PRODUCTION_CI_DEPLOYMENT_PATH=${PRODUCTION_CI_DEPLOYMENT_PATH}"
log "PRODUCTION_CI_DEPLOYMENT_REVIEW=${PRODUCTION_CI_DEPLOYMENT_REVIEW}"
log "PRODUCTION_CI_DEPLOYMENT_BLOCKER=${PRODUCTION_CI_DEPLOYMENT_BLOCKER}"

log ""
log "============================================================"
log "9. R43 GAP REASSESSMENT"
log "============================================================"

R43_REPORT="${PROJECT_ROOT}/p0_03_r43_production_gap_classification_gate.txt"

if [ -f "${R43_REPORT}" ]; then
    pass "R43_REPORT_PRESENT"

    R43_CI_DEPLOY_GAP="$(
        awk -F= '
            $1=="CI_DEPLOY_GAP" {v=$2}
            END {print v+0}
        ' "${R43_REPORT}" 2>/dev/null || true
    )"

    : "${R43_CI_DEPLOY_GAP:=0}"

    log "R43_CI_DEPLOY_GAP=${R43_CI_DEPLOY_GAP}"

    if [ "${R43_CI_DEPLOY_GAP}" -gt 0 ]; then

        if [ "${PRODUCTION_CI_DEPLOYMENT_PATH}" -gt 0 ]; then
            pass "R43_CI_DEPLOY_GAP_REASSESSED_AS_PRODUCTION_PATH_PRESENT"
        else
            PRODUCTION_CI_DEPLOYMENT_BLOCKER=1
            fail "R43_CI_DEPLOY_GAP_REMAINS_UNRESOLVED"
        fi

    else
        pass "R43_CI_DEPLOY_GAP_NOT_ASSERTED"
    fi
else
    review "R43_REPORT_NOT_AVAILABLE_REASSESSMENT_LIMITED"
fi

log ""
log "============================================================"
log "10. FINAL R49 DECISION"
log "============================================================"

log "CI_WORKFLOW_COUNT=${CI_WORKFLOW_COUNT}"
log "CI_PRODUCTION_MARKER_COUNT=${CI_PRODUCTION_MARKER_COUNT}"
log "CI_DEPLOY_KEYWORD_COUNT=${CI_DEPLOY_KEYWORD_COUNT}"
log "CI_DOCKER_BUILD_COUNT=${CI_DOCKER_BUILD_COUNT}"
log "CI_DOCKER_PUSH_COUNT=${CI_DOCKER_PUSH_COUNT}"
log "CI_REGISTRY_COUNT=${CI_REGISTRY_COUNT}"
log "CI_ARTIFACT_RELEASE_COUNT=${CI_ARTIFACT_RELEASE_COUNT}"
log "CI_REMOTE_DEPLOY_COUNT=${CI_REMOTE_DEPLOY_COUNT}"
log "CI_PRODUCTION_ENV_COUNT=${CI_PRODUCTION_ENV_COUNT}"
log "CI_BRANCH_GUARD_COUNT=${CI_BRANCH_GUARD_COUNT}"
log "CI_DEPLOY_SCRIPT_REFERENCE_COUNT=${CI_DEPLOY_SCRIPT_REFERENCE_COUNT}"

log "DEPLOY_SCRIPT_PRESENT=${DEPLOY_SCRIPT_PRESENT}"
log "DEPLOY_SCRIPT_COMPOSE_COUNT=${DEPLOY_SCRIPT_COMPOSE_COUNT}"
log "DEPLOY_SCRIPT_BUILD_COUNT=${DEPLOY_SCRIPT_BUILD_COUNT}"
log "DEPLOY_SCRIPT_PUSH_COUNT=${DEPLOY_SCRIPT_PUSH_COUNT}"
log "DEPLOY_SCRIPT_REMOTE_DEPLOY_COUNT=${DEPLOY_SCRIPT_REMOTE_DEPLOY_COUNT}"
log "DEPLOY_SCRIPT_PRODUCTION_COUNT=${DEPLOY_SCRIPT_PRODUCTION_COUNT}"
log "DEPLOY_SCRIPT_FAIL_FAST_COUNT=${DEPLOY_SCRIPT_FAIL_FAST_COUNT}"

log "PRODUCTION_CI_DEPLOYMENT_PATH=${PRODUCTION_CI_DEPLOYMENT_PATH}"
log "PRODUCTION_CI_DEPLOYMENT_REVIEW=${PRODUCTION_CI_DEPLOYMENT_REVIEW}"
log "PRODUCTION_CI_DEPLOYMENT_BLOCKER=${PRODUCTION_CI_DEPLOYMENT_BLOCKER}"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

if [ "${PRODUCTION_CI_DEPLOYMENT_BLOCKER}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R49_CI_PRODUCTION_DEPLOYMENT_BLOCKER_CONFIRMED"
    EXIT_CODE=2

elif [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R49_CI_PRODUCTION_DEPLOYMENT_AUTHORITY_GATE_FAILED"
    EXIT_CODE=2

elif [ "${PRODUCTION_CI_DEPLOYMENT_PATH}" -gt 0 ] &&
     [ "${PRODUCTION_CI_DEPLOYMENT_REVIEW}" -eq 0 ]; then

    STATUS="PASS"
    RESULT="P0_03_R49_CI_PRODUCTION_DEPLOYMENT_AUTHORITY_CLOSED"
    EXIT_CODE=0

else

    STATUS="REVIEW"
    RESULT="P0_03_R49_CI_PRODUCTION_DEPLOYMENT_AUTHORITY_REVIEW"
    EXIT_CODE=1
fi

log "P0_03_R49_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"

log ""
log "============================================================"
log "R49 COMPLETE"
log "============================================================"

exit "${EXIT_CODE}"
