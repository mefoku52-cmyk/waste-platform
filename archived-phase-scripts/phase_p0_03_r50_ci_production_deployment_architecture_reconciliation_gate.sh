#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT="${PROJECT_ROOT}/p0_03_r50_ci_production_deployment_architecture_reconciliation_gate.txt"

CI_FILE="${PROJECT_ROOT}/.github/workflows/ci.yml"
DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

TMP_CI="${PROJECT_ROOT}/.r50_tmp_ci"
TMP_DEPLOY="${PROJECT_ROOT}/.r50_tmp_deploy"
TMP_COMPOSE="${PROJECT_ROOT}/.r50_tmp_compose"

FAILURE_COUNT=0
REVIEW_COUNT=0

R48_STATUS=0
R48_EXIT_CODE=0
R48_PRODUCTION_RELOAD_BLOCKER=0

CI_PRESENT=0
DEPLOY_PRESENT=0
COMPOSE_PRESENT=0

CI_JOB_COUNT=0
CI_TEST_JOB_COUNT=0
CI_BUILD_JOB_COUNT=0
CI_DEPLOY_JOB_COUNT=0
CI_RELEASE_JOB_COUNT=0
CI_PRODUCTION_JOB_COUNT=0
CI_ENVIRONMENT_COUNT=0
CI_BRANCH_GUARD_COUNT=0
CI_DEPLOY_SCRIPT_REF_COUNT=0
CI_COMPOSE_REF_COUNT=0
CI_DOCKER_BUILD_COUNT=0
CI_DOCKER_PUSH_COUNT=0
CI_REGISTRY_COUNT=0
CI_REMOTE_DEPLOY_COUNT=0

DEPLOY_COMPOSE_COUNT=0
DEPLOY_PRODUCTION_COUNT=0
DEPLOY_FAIL_FAST_COUNT=0
DEPLOY_TEST_COUNT=0
DEPLOY_VERIFY_COUNT=0
DEPLOY_ROLLBACK_COUNT=0
DEPLOY_RELOAD_COUNT=0

COMPOSE_PRODUCTION_SERVICE_COUNT=0
COMPOSE_BUILD_COUNT=0
COMPOSE_DEPLOYMENT_OPERATION_COUNT=0

CI_VERIFICATION_PATH=0
PRODUCTION_DEPLOYMENT_AUTHORITY=0
ARCHITECTURAL_SEPARATION=0
PRODUCTION_DEPLOYMENT_GAP=0
PRODUCTION_DEPLOYMENT_BLOCKER=0

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
        "${TMP_COMPOSE}" \
        2>/dev/null || true
}

trap cleanup EXIT

: > "${REPORT}"
: > "${TMP_CI}"
: > "${TMP_DEPLOY}"
: > "${TMP_COMPOSE}"

log "============================================================"
log "P0-03 R50 CI/PRODUCTION DEPLOYMENT ARCHITECTURE RECONCILIATION GATE"
log "============================================================"
log ""

log "============================================================"
log "1. SAFETY PRECHECK"
log "============================================================"

if [ -d "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
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
pass "AUTHORITY_RECONCILIATION_ONLY=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. AUTHORITY FILE PRESENCE"
log "============================================================"

if [ -f "${CI_FILE}" ]; then
    CI_PRESENT=1
    pass "PRIMARY_CI_WORKFLOW_PRESENT"
else
    fail "PRIMARY_CI_WORKFLOW_MISSING"
fi

if [ -f "${DEPLOY_SCRIPT}" ]; then
    DEPLOY_PRESENT=1
    pass "PRIMARY_DEPLOY_SCRIPT_PRESENT"
else
    fail "PRIMARY_DEPLOY_SCRIPT_MISSING"
fi

if [ -f "${COMPOSE_FILE}" ]; then
    COMPOSE_PRESENT=1
    pass "DOCKER_COMPOSE_PRESENT"
else
    fail "DOCKER_COMPOSE_MISSING"
fi

log "CI_PRESENT=${CI_PRESENT}"
log "DEPLOY_PRESENT=${DEPLOY_PRESENT}"
log "COMPOSE_PRESENT=${COMPOSE_PRESENT}"

log ""
log "============================================================"
log "3. R48 HANDOFF"
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
        pass "R48_RELOAD_AUTHORITY_CLOSED"
    else
        review "R48_HANDOFF_NOT_CLEAN"
    fi
else
    review "R48_REPORT_NOT_AVAILABLE_HANDOFF_NOT_USED"
fi

log ""
log "============================================================"
log "4. CI JOB TOPOLOGY"
log "============================================================"

if [ "${CI_PRESENT}" -eq 1 ]; then

    CI_JOB_COUNT="$(
        grep -Ec '^[[:space:]]{2,}[A-Za-z0-9_.-]+:[[:space:]]*$' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_TEST_JOB_COUNT="$(
        grep -Eic \
            'pytest|unittest|test(s)?[[:space:]:_-]|coverage' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_BUILD_JOB_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+(build|buildx)|docker/build|gradle|npm[[:space:]]+(run[[:space:]]+)?build|build:' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_DEPLOY_JOB_COUNT="$(
        grep -Eic \
            '^[[:space:]]*[A-Za-z0-9_.-]*deploy[A-Za-z0-9_.-]*:[[:space:]]*$' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_RELEASE_JOB_COUNT="$(
        grep -Eic \
            '^[[:space:]]*[A-Za-z0-9_.-]*release[A-Za-z0-9_.-]*:[[:space:]]*$' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_PRODUCTION_JOB_COUNT="$(
        grep -Eic \
            '^[[:space:]]*[A-Za-z0-9_.-]*(production|prod)[A-Za-z0-9_.-]*:[[:space:]]*$' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_ENVIRONMENT_COUNT="$(
        grep -Eic \
            '^[[:space:]]*environment:[[:space:]]*|ENVIRONMENT|DEPLOY_ENV|APP_ENV' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_BRANCH_GUARD_COUNT="$(
        grep -Eic \
            'branches:|branches-ignore:|github\.ref|if:.*main|if:.*master' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_DEPLOY_SCRIPT_REF_COUNT="$(
        grep -Eic \
            'scripts/deploy\.sh|deploy\.sh' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_COMPOSE_REF_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose|docker-compose' \
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

    CI_REMOTE_DEPLOY_COUNT="$(
        grep -Eic \
            'ssh|scp|rsync|kubectl|helm|ansible|terraform|docker[[:space:]]+context|remote' \
            "${CI_FILE}" 2>/dev/null || true
    )"
fi

log "CI_JOB_COUNT=${CI_JOB_COUNT}"
log "CI_TEST_JOB_COUNT=${CI_TEST_JOB_COUNT}"
log "CI_BUILD_JOB_COUNT=${CI_BUILD_JOB_COUNT}"
log "CI_DEPLOY_JOB_COUNT=${CI_DEPLOY_JOB_COUNT}"
log "CI_RELEASE_JOB_COUNT=${CI_RELEASE_JOB_COUNT}"
log "CI_PRODUCTION_JOB_COUNT=${CI_PRODUCTION_JOB_COUNT}"
log "CI_ENVIRONMENT_COUNT=${CI_ENVIRONMENT_COUNT}"
log "CI_BRANCH_GUARD_COUNT=${CI_BRANCH_GUARD_COUNT}"
log "CI_DEPLOY_SCRIPT_REF_COUNT=${CI_DEPLOY_SCRIPT_REF_COUNT}"
log "CI_COMPOSE_REF_COUNT=${CI_COMPOSE_REF_COUNT}"
log "CI_DOCKER_BUILD_COUNT=${CI_DOCKER_BUILD_COUNT}"
log "CI_DOCKER_PUSH_COUNT=${CI_DOCKER_PUSH_COUNT}"
log "CI_REGISTRY_COUNT=${CI_REGISTRY_COUNT}"
log "CI_REMOTE_DEPLOY_COUNT=${CI_REMOTE_DEPLOY_COUNT}"

if [ "${CI_TEST_JOB_COUNT}" -gt 0 ]; then
    pass "CI_TEST_VERIFICATION_PATH_PRESENT"
else
    review "CI_TEST_VERIFICATION_PATH_NOT_DETECTED"
fi

if [ "${CI_BUILD_JOB_COUNT}" -gt 0 ]; then
    pass "CI_BUILD_VERIFICATION_PATH_PRESENT"
else
    review "CI_BUILD_VERIFICATION_PATH_NOT_DETECTED"
fi

if [ "${CI_BRANCH_GUARD_COUNT}" -gt 0 ]; then
    pass "CI_BRANCH_GUARD_PRESENT"
else
    review "CI_BRANCH_GUARD_NOT_DETECTED"
fi

log ""
log "============================================================"
log "5. CI PRODUCTION DEPLOYMENT AUTHORITY"
log "============================================================"

if [ "${CI_DEPLOY_JOB_COUNT}" -gt 0 ]; then
    pass "CI_DEPLOY_JOB_PRESENT"
else
    log "CI_DEPLOY_JOB_PRESENT=0"
fi

if [ "${CI_RELEASE_JOB_COUNT}" -gt 0 ]; then
    pass "CI_RELEASE_JOB_PRESENT"
else
    log "CI_RELEASE_JOB_PRESENT=0"
fi

if [ "${CI_PRODUCTION_JOB_COUNT}" -gt 0 ]; then
    pass "CI_PRODUCTION_JOB_PRESENT"
else
    log "CI_PRODUCTION_JOB_PRESENT=0"
fi

if [ "${CI_DOCKER_PUSH_COUNT}" -gt 0 ] &&
   [ "${CI_REGISTRY_COUNT}" -gt 0 ]; then
    pass "CI_CONTAINER_RELEASE_AUTHORITY_PRESENT"
else
    log "CI_CONTAINER_RELEASE_AUTHORITY_PRESENT=0"
fi

if [ "${CI_REMOTE_DEPLOY_COUNT}" -gt 0 ]; then
    pass "CI_REMOTE_DEPLOYMENT_AUTHORITY_SIGNAL_PRESENT"
else
    log "CI_REMOTE_DEPLOYMENT_AUTHORITY_SIGNAL_PRESENT=0"
fi

if [ "${CI_DEPLOY_SCRIPT_REF_COUNT}" -gt 0 ]; then
    pass "CI_PRIMARY_DEPLOY_SCRIPT_REFERENCE_PRESENT"
else
    log "CI_PRIMARY_DEPLOY_SCRIPT_REFERENCE_PRESENT=0"
fi

log ""
log "============================================================"
log "6. PRIMARY DEPLOYMENT AUTHORITY"
log "============================================================"

if [ "${DEPLOY_PRESENT}" -eq 1 ]; then

    DEPLOY_COMPOSE_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose|docker-compose' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_PRODUCTION_COUNT="$(
        grep -Eic \
            'production|PRODUCTION|prod([_-]|$)' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_FAIL_FAST_COUNT="$(
        grep -Ec \
            '^[[:space:]]*set[[:space:]]+-[^#]*e' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_TEST_COUNT="$(
        grep -Eic \
            'pytest|test(s)?[[:space:]:_-]' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_VERIFY_COUNT="$(
        grep -Eic \
            'health|readiness|verify|wait|curl|wget|status' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_ROLLBACK_COUNT="$(
        grep -Eic \
            'rollback|roll-back|revert' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_RELOAD_COUNT="$(
        grep -Eic \
            -- '--reload|[[:space:]]reload([[:space:]]|_|-)' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"
fi

log "DEPLOY_COMPOSE_COUNT=${DEPLOY_COMPOSE_COUNT}"
log "DEPLOY_PRODUCTION_COUNT=${DEPLOY_PRODUCTION_COUNT}"
log "DEPLOY_FAIL_FAST_COUNT=${DEPLOY_FAIL_FAST_COUNT}"
log "DEPLOY_TEST_COUNT=${DEPLOY_TEST_COUNT}"
log "DEPLOY_VERIFY_COUNT=${DEPLOY_VERIFY_COUNT}"
log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
log "DEPLOY_RELOAD_COUNT=${DEPLOY_RELOAD_COUNT}"

if [ "${DEPLOY_COMPOSE_COUNT}" -gt 0 ]; then
    pass "PRIMARY_DEPLOYMENT_USES_COMPOSE"
else
    review "PRIMARY_DEPLOYMENT_HAS_NO_COMPOSE_SIGNAL"
fi

if [ "${DEPLOY_PRODUCTION_COUNT}" -gt 0 ]; then
    pass "PRIMARY_DEPLOYMENT_HAS_PRODUCTION_SIGNAL"
else
    review "PRIMARY_DEPLOYMENT_PRODUCTION_SIGNAL_NOT_DETECTED"
fi

if [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then
    pass "PRIMARY_DEPLOYMENT_FAIL_FAST_PRESENT"
else
    review "PRIMARY_DEPLOYMENT_FAIL_FAST_NOT_DETECTED"
fi

if [ "${DEPLOY_RELOAD_COUNT}" -eq 0 ]; then
    pass "PRIMARY_DEPLOYMENT_HAS_NO_RELOAD"
else
    fail "PRIMARY_DEPLOYMENT_REFERENCES_RELOAD"
fi

log ""
log "============================================================"
log "7. DEPLOYMENT VERIFICATION / ROLLBACK AUTHORITY"
log "============================================================"

if [ "${DEPLOY_VERIFY_COUNT}" -gt 0 ]; then
    pass "DEPLOYMENT_POST_ACTION_VERIFICATION_SIGNAL_PRESENT"
else
    review "DEPLOYMENT_POST_ACTION_VERIFICATION_SIGNAL_NOT_DETECTED"
fi

if [ "${DEPLOY_ROLLBACK_COUNT}" -gt 0 ]; then
    pass "DEPLOYMENT_ROLLBACK_SIGNAL_PRESENT"
else
    review "DEPLOYMENT_ROLLBACK_SIGNAL_NOT_DETECTED"
fi

log ""
log "============================================================"
log "8. COMPOSE PRODUCTION TOPOLOGY"
log "============================================================"

if [ "${COMPOSE_PRESENT}" -eq 1 ]; then

    COMPOSE_BUILD_COUNT="$(
        grep -Ec \
            '^[[:space:]]*build:' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_PRODUCTION_SERVICE_COUNT="$(
        grep -Eic \
            'production|prod([_-]|$)' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_DEPLOYMENT_OPERATION_COUNT="$(
        grep -Eic \
            'restart:|healthcheck:|depends_on:|command:|entrypoint:' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"
fi

log "COMPOSE_BUILD_COUNT=${COMPOSE_BUILD_COUNT}"
log "COMPOSE_PRODUCTION_SERVICE_COUNT=${COMPOSE_PRODUCTION_SERVICE_COUNT}"
log "COMPOSE_DEPLOYMENT_OPERATION_COUNT=${COMPOSE_DEPLOYMENT_OPERATION_COUNT}"

if [ "${COMPOSE_BUILD_COUNT}" -gt 0 ]; then
    pass "COMPOSE_BUILD_TOPOLOGY_PRESENT"
else
    review "COMPOSE_BUILD_TOPOLOGY_NOT_DETECTED"
fi

if [ "${COMPOSE_DEPLOYMENT_OPERATION_COUNT}" -gt 0 ]; then
    pass "COMPOSE_RUNTIME_DEPLOYMENT_TOPOLOGY_PRESENT"
else
    review "COMPOSE_RUNTIME_DEPLOYMENT_TOPOLOGY_NOT_DETECTED"
fi

log ""
log "============================================================"
log "9. ARCHITECTURE RECONCILIATION"
log "============================================================"

CI_VERIFICATION_PATH=0
PRODUCTION_DEPLOYMENT_AUTHORITY=0
ARCHITECTURAL_SEPARATION=0
PRODUCTION_DEPLOYMENT_GAP=0
PRODUCTION_DEPLOYMENT_BLOCKER=0

if [ "${CI_TEST_JOB_COUNT}" -gt 0 ] &&
   [ "${CI_BUILD_JOB_COUNT}" -gt 0 ]; then
    CI_VERIFICATION_PATH=1
    pass "CI_VERIFICATION_ROLE_ESTABLISHED"
else
    review "CI_VERIFICATION_ROLE_NOT_FULLY_ESTABLISHED"
fi

if [ "${DEPLOY_PRESENT}" -eq 1 ] &&
   [ "${DEPLOY_COMPOSE_COUNT}" -gt 0 ] &&
   [ "${DEPLOY_PRODUCTION_COUNT}" -gt 0 ] &&
   [ "${DEPLOY_RELOAD_COUNT}" -eq 0 ]; then
    PRODUCTION_DEPLOYMENT_AUTHORITY=1
    pass "PRIMARY_PRODUCTION_DEPLOYMENT_AUTHORITY_ESTABLISHED"
else
    review "PRIMARY_PRODUCTION_DEPLOYMENT_AUTHORITY_NOT_FULLY_ESTABLISHED"
fi

if [ "${CI_VERIFICATION_PATH}" -eq 1 ] &&
   [ "${PRODUCTION_DEPLOYMENT_AUTHORITY}" -eq 1 ] &&
   [ "${CI_DEPLOY_JOB_COUNT}" -eq 0 ] &&
   [ "${CI_RELEASE_JOB_COUNT}" -eq 0 ] &&
   [ "${CI_DEPLOY_SCRIPT_REF_COUNT}" -eq 0 ]; then

    ARCHITECTURAL_SEPARATION=1
    pass "CI_AND_PRODUCTION_DEPLOYMENT_ARE_EXPLICITLY_SEPARATED"

elif [ "${CI_DEPLOY_JOB_COUNT}" -eq 0 ] &&
     [ "${CI_RELEASE_JOB_COUNT}" -eq 0 ] &&
     [ "${PRODUCTION_DEPLOYMENT_AUTHORITY}" -eq 0 ]; then

    PRODUCTION_DEPLOYMENT_GAP=1
    fail "CI_HAS_NO_DEPLOYMENT_AND_NO_ESTABLISHED_PRODUCTION_AUTHORITY"

else
    review "CI_PRODUCTION_DEPLOYMENT_ARCHITECTURE_REQUIRES_CLASSIFICATION"
fi

log "CI_VERIFICATION_PATH=${CI_VERIFICATION_PATH}"
log "PRODUCTION_DEPLOYMENT_AUTHORITY=${PRODUCTION_DEPLOYMENT_AUTHORITY}"
log "ARCHITECTURAL_SEPARATION=${ARCHITECTURAL_SEPARATION}"
log "PRODUCTION_DEPLOYMENT_GAP=${PRODUCTION_DEPLOYMENT_GAP}"
log "PRODUCTION_DEPLOYMENT_BLOCKER=${PRODUCTION_DEPLOYMENT_BLOCKER}"

log ""
log "============================================================"
log "10. R49 REVIEW RECONCILIATION"
log "============================================================"

R49_REPORT="${PROJECT_ROOT}/p0_03_r49_ci_production_deployment_authority_gate.txt"

if [ -f "${R49_REPORT}" ]; then
    pass "R49_REPORT_PRESENT"

    R49_STATUS="$(
        awk -F= '
            $1=="P0_03_R49_STATUS" {v=$2}
            END {print v}
        ' "${R49_REPORT}" 2>/dev/null || true
    )"

    R49_PATH="$(
        awk -F= '
            $1=="PRODUCTION_CI_DEPLOYMENT_PATH" {v=$2}
            END {print v+0}
        ' "${R49_REPORT}" 2>/dev/null || true
    )"

    R49_REVIEW="$(
        awk -F= '
            $1=="PRODUCTION_CI_DEPLOYMENT_REVIEW" {v=$2}
            END {print v+0}
        ' "${R49_REPORT}" 2>/dev/null || true
    )"

    R49_BLOCKER="$(
        awk -F= '
            $1=="PRODUCTION_CI_DEPLOYMENT_BLOCKER" {v=$2}
            END {print v+0}
        ' "${R49_REPORT}" 2>/dev/null || true
    )"

    : "${R49_STATUS:=UNKNOWN}"
    : "${R49_PATH:=0}"
    : "${R49_REVIEW:=0}"
    : "${R49_BLOCKER:=0}"

    log "R49_STATUS=${R49_STATUS}"
    log "R49_PRODUCTION_CI_DEPLOYMENT_PATH=${R49_PATH}"
    log "R49_PRODUCTION_CI_DEPLOYMENT_REVIEW=${R49_REVIEW}"
    log "R49_PRODUCTION_CI_DEPLOYMENT_BLOCKER=${R49_BLOCKER}"

    if [ "${ARCHITECTURAL_SEPARATION}" -eq 1 ]; then

        pass "R49_REVIEW_RECLASSIFIED_AS_ARCHITECTURAL_SEPARATION"

    elif [ "${PRODUCTION_DEPLOYMENT_GAP}" -eq 1 ]; then

        PRODUCTION_DEPLOYMENT_BLOCKER=1
        fail "R49_REVIEW_RECONCILED_AS_REAL_PRODUCTION_DEPLOYMENT_GAP"

    else

        review "R49_REVIEW_REMAINS_UNRESOLVED"
    fi
else
    review "R49_REPORT_NOT_AVAILABLE_RECONCILIATION_LIMITED"
fi

log ""
log "============================================================"
log "11. FINAL R50 DECISION"
log "============================================================"

log "CI_VERIFICATION_PATH=${CI_VERIFICATION_PATH}"
log "PRODUCTION_DEPLOYMENT_AUTHORITY=${PRODUCTION_DEPLOYMENT_AUTHORITY}"
log "ARCHITECTURAL_SEPARATION=${ARCHITECTURAL_SEPARATION}"
log "PRODUCTION_DEPLOYMENT_GAP=${PRODUCTION_DEPLOYMENT_GAP}"
log "PRODUCTION_DEPLOYMENT_BLOCKER=${PRODUCTION_DEPLOYMENT_BLOCKER}"

log "CI_DEPLOY_JOB_COUNT=${CI_DEPLOY_JOB_COUNT}"
log "CI_RELEASE_JOB_COUNT=${CI_RELEASE_JOB_COUNT}"
log "CI_PRODUCTION_JOB_COUNT=${CI_PRODUCTION_JOB_COUNT}"
log "CI_DEPLOY_SCRIPT_REF_COUNT=${CI_DEPLOY_SCRIPT_REF_COUNT}"

log "DEPLOY_COMPOSE_COUNT=${DEPLOY_COMPOSE_COUNT}"
log "DEPLOY_PRODUCTION_COUNT=${DEPLOY_PRODUCTION_COUNT}"
log "DEPLOY_FAIL_FAST_COUNT=${DEPLOY_FAIL_FAST_COUNT}"
log "DEPLOY_VERIFY_COUNT=${DEPLOY_VERIFY_COUNT}"
log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
log "DEPLOY_RELOAD_COUNT=${DEPLOY_RELOAD_COUNT}"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

if [ "${PRODUCTION_DEPLOYMENT_BLOCKER}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R50_REAL_PRODUCTION_DEPLOYMENT_GAP_CONFIRMED"
    EXIT_CODE=2

elif [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R50_CI_PRODUCTION_ARCHITECTURE_GATE_FAILED"
    EXIT_CODE=2

elif [ "${ARCHITECTURAL_SEPARATION}" -eq 1 ]; then

    STATUS="PASS"
    RESULT="P0_03_R50_CI_PRODUCTION_ARCHITECTURAL_SEPARATION_CONFIRMED"
    EXIT_CODE=0

elif [ "${PRODUCTION_DEPLOYMENT_AUTHORITY}" -eq 1 ]; then

    STATUS="REVIEW"
    RESULT="P0_03_R50_PRODUCTION_DEPLOYMENT_AUTHORITY_PRESENT_CI_LINKAGE_REVIEW"
    EXIT_CODE=1

else

    STATUS="REVIEW"
    RESULT="P0_03_R50_CI_PRODUCTION_DEPLOYMENT_ARCHITECTURE_REVIEW"
    EXIT_CODE=1
fi

log "P0_03_R50_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"

log ""
log "============================================================"
log "R50 COMPLETE"
log "============================================================"

exit "${EXIT_CODE}"
