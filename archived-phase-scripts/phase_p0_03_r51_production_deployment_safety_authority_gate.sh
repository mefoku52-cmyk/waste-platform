#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT="${PROJECT_ROOT}/p0_03_r51_production_deployment_safety_authority_gate.txt"

CI_FILE="${PROJECT_ROOT}/.github/workflows/ci.yml"
DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

R50_REPORT="${PROJECT_ROOT}/p0_03_r50_ci_production_deployment_architecture_reconciliation_gate.txt"

TMP_DEPLOY="${PROJECT_ROOT}/.r51_tmp_deploy"
TMP_COMPOSE="${PROJECT_ROOT}/.r51_tmp_compose"
TMP_CI="${PROJECT_ROOT}/.r51_tmp_ci"

FAILURE_COUNT=0
REVIEW_COUNT=0

R50_STATUS="UNKNOWN"
R50_EXIT_CODE=0
R50_ARCHITECTURAL_SEPARATION=0
R50_PRODUCTION_DEPLOYMENT_AUTHORITY=0
R50_PRODUCTION_DEPLOYMENT_GAP=0
R50_PRODUCTION_DEPLOYMENT_BLOCKER=0

DEPLOY_PRESENT=0
COMPOSE_PRESENT=0
CI_PRESENT=0

DEPLOY_FAIL_FAST_COUNT=0
DEPLOY_COMPOSE_COUNT=0
DEPLOY_PRODUCTION_COUNT=0
DEPLOY_VERIFY_COUNT=0
DEPLOY_HEALTH_COUNT=0
DEPLOY_READINESS_COUNT=0
DEPLOY_CURL_COUNT=0
DEPLOY_WGET_COUNT=0
DEPLOY_WAIT_COUNT=0
DEPLOY_STATUS_COUNT=0
DEPLOY_EXIT_CODE_CHECK_COUNT=0
DEPLOY_ROLLBACK_COUNT=0
DEPLOY_REVERT_COUNT=0
DEPLOY_BACKUP_COUNT=0
DEPLOY_PREVIOUS_IMAGE_COUNT=0
DEPLOY_DOWN_COUNT=0
DEPLOY_UP_COUNT=0
DEPLOY_RESTART_COUNT=0
DEPLOY_RECREATE_COUNT=0

COMPOSE_HEALTHCHECK_COUNT=0
COMPOSE_HEALTHCHECK_TEST_COUNT=0
COMPOSE_DEPENDS_ON_COUNT=0
COMPOSE_RESTART_COUNT=0
COMPOSE_STOP_GRACE_COUNT=0
COMPOSE_ROLLING_SIGNAL_COUNT=0
COMPOSE_VERSION_SIGNAL_COUNT=0

CI_TEST_COUNT=0
CI_BUILD_COUNT=0
CI_DEPLOY_COUNT=0
CI_RELEASE_COUNT=0

POST_DEPLOY_VERIFICATION_AUTHORITY=0
FAIL_CLOSED_DEPLOYMENT_AUTHORITY=0
ROLLBACK_AUTHORITY=0
RECOVERY_AUTHORITY=0
DEPLOYMENT_SAFETY_GAP=0
DEPLOYMENT_SAFETY_BLOCKER=0

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
        "${TMP_DEPLOY}" \
        "${TMP_COMPOSE}" \
        "${TMP_CI}" \
        2>/dev/null || true
}

trap cleanup EXIT

: > "${REPORT}"
: > "${TMP_DEPLOY}"
: > "${TMP_COMPOSE}"
: > "${TMP_CI}"

log "============================================================"
log "P0-03 R51 PRODUCTION DEPLOYMENT SAFETY AUTHORITY GATE"
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
pass "DEPLOYMENT_SAFETY_ANALYSIS_ONLY=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. AUTHORITY FILE PRESENCE"
log "============================================================"

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

if [ -f "${CI_FILE}" ]; then
    CI_PRESENT=1
    pass "PRIMARY_CI_WORKFLOW_PRESENT"
else
    review "PRIMARY_CI_WORKFLOW_MISSING"
fi

log "DEPLOY_PRESENT=${DEPLOY_PRESENT}"
log "COMPOSE_PRESENT=${COMPOSE_PRESENT}"
log "CI_PRESENT=${CI_PRESENT}"

log ""
log "============================================================"
log "3. R50 HANDOFF"
log "============================================================"

if [ -f "${R50_REPORT}" ]; then

    pass "R50_REPORT_PRESENT"

    R50_STATUS="$(
        awk -F= '
            $1=="P0_03_R50_STATUS" {v=$2}
            END {print v}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_EXIT_CODE="$(
        awk -F= '
            $1=="EXIT_CODE" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_ARCHITECTURAL_SEPARATION="$(
        awk -F= '
            $1=="ARCHITECTURAL_SEPARATION" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_PRODUCTION_DEPLOYMENT_AUTHORITY="$(
        awk -F= '
            $1=="PRODUCTION_DEPLOYMENT_AUTHORITY" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_PRODUCTION_DEPLOYMENT_GAP="$(
        awk -F= '
            $1=="PRODUCTION_DEPLOYMENT_GAP" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_PRODUCTION_DEPLOYMENT_BLOCKER="$(
        awk -F= '
            $1=="PRODUCTION_DEPLOYMENT_BLOCKER" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    : "${R50_STATUS:=UNKNOWN}"
    : "${R50_EXIT_CODE:=0}"
    : "${R50_ARCHITECTURAL_SEPARATION:=0}"
    : "${R50_PRODUCTION_DEPLOYMENT_AUTHORITY:=0}"
    : "${R50_PRODUCTION_DEPLOYMENT_GAP:=0}"
    : "${R50_PRODUCTION_DEPLOYMENT_BLOCKER:=0}"

    log "R50_STATUS=${R50_STATUS}"
    log "R50_EXIT_CODE=${R50_EXIT_CODE}"
    log "R50_ARCHITECTURAL_SEPARATION=${R50_ARCHITECTURAL_SEPARATION}"
    log "R50_PRODUCTION_DEPLOYMENT_AUTHORITY=${R50_PRODUCTION_DEPLOYMENT_AUTHORITY}"
    log "R50_PRODUCTION_DEPLOYMENT_GAP=${R50_PRODUCTION_DEPLOYMENT_GAP}"
    log "R50_PRODUCTION_DEPLOYMENT_BLOCKER=${R50_PRODUCTION_DEPLOYMENT_BLOCKER}"

    if [ "${R50_STATUS}" = "PASS" ] &&
       [ "${R50_EXIT_CODE}" -eq 0 ] &&
       [ "${R50_ARCHITECTURAL_SEPARATION}" -eq 1 ] &&
       [ "${R50_PRODUCTION_DEPLOYMENT_AUTHORITY}" -eq 1 ] &&
       [ "${R50_PRODUCTION_DEPLOYMENT_GAP}" -eq 0 ] &&
       [ "${R50_PRODUCTION_DEPLOYMENT_BLOCKER}" -eq 0 ]; then

        pass "R50_ARCHITECTURE_HANDOFF_ACCEPTED"

    else
        review "R50_HANDOFF_NOT_CLEAN"
    fi

else
    review "R50_REPORT_NOT_AVAILABLE_HANDOFF_NOT_USED"
fi

log ""
log "============================================================"
log "4. PRIMARY DEPLOY SCRIPT STATIC ANALYSIS"
log "============================================================"

if [ "${DEPLOY_PRESENT}" -eq 1 ]; then

    DEPLOY_FAIL_FAST_COUNT="$(
        grep -Ec \
            '^[[:space:]]*set[[:space:]]+-[^#]*e' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

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

    DEPLOY_VERIFY_COUNT="$(
        grep -Eic \
            'verify|verification|health|readiness|ready|liveness|status|wait|check' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_HEALTH_COUNT="$(
        grep -Eic \
            'health|healthcheck|healthy' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_READINESS_COUNT="$(
        grep -Eic \
            'readiness|ready|readyz|readyz' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_CURL_COUNT="$(
        grep -Eic \
            '(^|[[:space:]])curl([[:space:]]|$)' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_WGET_COUNT="$(
        grep -Eic \
            '(^|[[:space:]])wget([[:space:]]|$)' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_WAIT_COUNT="$(
        grep -Eic \
            'wait|sleep|until|retry|retries|timeout' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_STATUS_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose.*ps|docker[[:space:]]+compose.*status|docker[[:space:]]+ps' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_EXIT_CODE_CHECK_COUNT="$(
        grep -Ec \
            '(\$[?]|PIPESTATUS|exit[[:space:]]+[0-9]+|if[[:space:]].*\$[?])' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_ROLLBACK_COUNT="$(
        grep -Eic \
            'rollback|roll-back|roll_back' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_REVERT_COUNT="$(
        grep -Eic \
            'revert|previous|restore|recover|recovery' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_BACKUP_COUNT="$(
        grep -Eic \
            'backup|snapshot' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_PREVIOUS_IMAGE_COUNT="$(
        grep -Eic \
            'previous.*image|old.*image|rollback.*image|image.*rollback' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_DOWN_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose.*down' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_UP_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose.*up' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_RESTART_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose.*restart' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_RECREATE_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose.*(recreate|force-recreate)' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"
fi

log "DEPLOY_FAIL_FAST_COUNT=${DEPLOY_FAIL_FAST_COUNT}"
log "DEPLOY_COMPOSE_COUNT=${DEPLOY_COMPOSE_COUNT}"
log "DEPLOY_PRODUCTION_COUNT=${DEPLOY_PRODUCTION_COUNT}"
log "DEPLOY_VERIFY_COUNT=${DEPLOY_VERIFY_COUNT}"
log "DEPLOY_HEALTH_COUNT=${DEPLOY_HEALTH_COUNT}"
log "DEPLOY_READINESS_COUNT=${DEPLOY_READINESS_COUNT}"
log "DEPLOY_CURL_COUNT=${DEPLOY_CURL_COUNT}"
log "DEPLOY_WGET_COUNT=${DEPLOY_WGET_COUNT}"
log "DEPLOY_WAIT_COUNT=${DEPLOY_WAIT_COUNT}"
log "DEPLOY_STATUS_COUNT=${DEPLOY_STATUS_COUNT}"
log "DEPLOY_EXIT_CODE_CHECK_COUNT=${DEPLOY_EXIT_CODE_CHECK_COUNT}"
log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
log "DEPLOY_REVERT_COUNT=${DEPLOY_REVERT_COUNT}"
log "DEPLOY_BACKUP_COUNT=${DEPLOY_BACKUP_COUNT}"
log "DEPLOY_PREVIOUS_IMAGE_COUNT=${DEPLOY_PREVIOUS_IMAGE_COUNT}"
log "DEPLOY_DOWN_COUNT=${DEPLOY_DOWN_COUNT}"
log "DEPLOY_UP_COUNT=${DEPLOY_UP_COUNT}"
log "DEPLOY_RESTART_COUNT=${DEPLOY_RESTART_COUNT}"
log "DEPLOY_RECREATE_COUNT=${DEPLOY_RECREATE_COUNT}"

if [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then
    pass "DEPLOY_FAIL_FAST_PRESENT"
else
    fail "DEPLOY_FAIL_FAST_MISSING"
fi

if [ "${DEPLOY_COMPOSE_COUNT}" -gt 0 ]; then
    pass "DEPLOY_COMPOSE_OPERATION_PRESENT"
else
    fail "DEPLOY_COMPOSE_OPERATION_MISSING"
fi

if [ "${DEPLOY_PRODUCTION_COUNT}" -gt 0 ]; then
    pass "DEPLOY_PRODUCTION_AUTHORITY_MARKER_PRESENT"
else
    review "DEPLOY_PRODUCTION_AUTHORITY_MARKER_NOT_DETECTED"
fi

if [ "${DEPLOY_HEALTH_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_READINESS_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_STATUS_COUNT}" -gt 0 ]; then
    pass "DEPLOY_POST_ACTION_VERIFICATION_SIGNAL_PRESENT"
else
    review "DEPLOY_POST_ACTION_VERIFICATION_SIGNAL_NOT_DETECTED"
fi

if [ "${DEPLOY_CURL_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_WGET_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_STATUS_COUNT}" -gt 0 ]; then
    pass "DEPLOY_ACTIVE_STATUS_CHECK_MECHANISM_PRESENT"
else
    review "DEPLOY_ACTIVE_STATUS_CHECK_MECHANISM_NOT_DETECTED"
fi

if [ "${DEPLOY_WAIT_COUNT}" -gt 0 ]; then
    pass "DEPLOY_WAIT_OR_RETRY_CONTROL_PRESENT"
else
    review "DEPLOY_WAIT_OR_RETRY_CONTROL_NOT_DETECTED"
fi

log ""
log "============================================================"
log "5. DEPLOYMENT FAIL-CLOSED SEMANTICS"
log "============================================================"

if [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then
    pass "FAIL_FAST_BASELINE_PRESENT"
else
    fail "FAIL_FAST_BASELINE_MISSING"
fi

if [ "${DEPLOY_EXIT_CODE_CHECK_COUNT}" -gt 0 ]; then
    pass "DEPLOY_EXIT_STATUS_HANDLING_SIGNAL_PRESENT"
else
    review "DEPLOY_EXIT_STATUS_HANDLING_NOT_DETECTED"
fi

if [ "${DEPLOY_VERIFY_COUNT}" -gt 0 ] &&
   [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then
    FAIL_CLOSED_DEPLOYMENT_AUTHORITY=1
    pass "FAIL_CLOSED_DEPLOYMENT_CONTROL_ESTABLISHED"
else
    review "FAIL_CLOSED_DEPLOYMENT_CONTROL_NOT_FULLY_ESTABLISHED"
fi

log "FAIL_CLOSED_DEPLOYMENT_AUTHORITY=${FAIL_CLOSED_DEPLOYMENT_AUTHORITY}"

log ""
log "============================================================"
log "6. COMPOSE HEALTH / READINESS AUTHORITY"
log "============================================================"

if [ "${COMPOSE_PRESENT}" -eq 1 ]; then

    COMPOSE_HEALTHCHECK_COUNT="$(
        grep -Ec \
            '^[[:space:]]*healthcheck:' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_HEALTHCHECK_TEST_COUNT="$(
        grep -Eic \
            'healthcheck:|test:[[:space:]]*\[|test:[[:space:]]*CMD|test:[[:space:]]*curl|test:[[:space:]]*wget' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_DEPENDS_ON_COUNT="$(
        grep -Ec \
            '^[[:space:]]*depends_on:' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_RESTART_COUNT="$(
        grep -Ec \
            '^[[:space:]]*restart:' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_STOP_GRACE_COUNT="$(
        grep -Eic \
            'stop_grace_period|stop_signal' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_ROLLING_SIGNAL_COUNT="$(
        grep -Eic \
            'rolling|zero[[:space:]-]?downtime|start-first|stop-first' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"

    COMPOSE_VERSION_SIGNAL_COUNT="$(
        grep -Eic \
            'image:[[:space:]]*[^$[:space:]]+:[A-Za-z0-9_.-]+|build:' \
            "${COMPOSE_FILE}" 2>/dev/null || true
    )"
fi

log "COMPOSE_HEALTHCHECK_COUNT=${COMPOSE_HEALTHCHECK_COUNT}"
log "COMPOSE_HEALTHCHECK_TEST_COUNT=${COMPOSE_HEALTHCHECK_TEST_COUNT}"
log "COMPOSE_DEPENDS_ON_COUNT=${COMPOSE_DEPENDS_ON_COUNT}"
log "COMPOSE_RESTART_COUNT=${COMPOSE_RESTART_COUNT}"
log "COMPOSE_STOP_GRACE_COUNT=${COMPOSE_STOP_GRACE_COUNT}"
log "COMPOSE_ROLLING_SIGNAL_COUNT=${COMPOSE_ROLLING_SIGNAL_COUNT}"
log "COMPOSE_VERSION_SIGNAL_COUNT=${COMPOSE_VERSION_SIGNAL_COUNT}"

if [ "${COMPOSE_HEALTHCHECK_COUNT}" -gt 0 ]; then
    pass "COMPOSE_HEALTHCHECK_AUTHORITY_PRESENT"
else
    fail "COMPOSE_HEALTHCHECK_AUTHORITY_MISSING"
fi

if [ "${COMPOSE_HEALTHCHECK_TEST_COUNT}" -gt 0 ]; then
    pass "COMPOSE_HEALTHCHECK_TEST_SIGNAL_PRESENT"
else
    fail "COMPOSE_HEALTHCHECK_TEST_SIGNAL_MISSING"
fi

if [ "${COMPOSE_DEPENDS_ON_COUNT}" -gt 0 ]; then
    pass "COMPOSE_DEPENDENCY_READINESS_ORDERING_PRESENT"
else
    review "COMPOSE_DEPENDENCY_READINESS_ORDERING_NOT_DETECTED"
fi

if [ "${COMPOSE_RESTART_COUNT}" -gt 0 ]; then
    pass "COMPOSE_RESTART_POLICY_PRESENT"
else
    review "COMPOSE_RESTART_POLICY_NOT_DETECTED"
fi

log ""
log "============================================================"
log "7. CI VERIFICATION BOUNDARY"
log "============================================================"

if [ "${CI_PRESENT}" -eq 1 ]; then

    CI_TEST_COUNT="$(
        grep -Eic \
            'pytest|unittest|test(s)?[[:space:]:_-]|coverage' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_BUILD_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+(build|buildx)|docker/build|build:' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_DEPLOY_COUNT="$(
        grep -Eic \
            'deploy|deployment' \
            "${CI_FILE}" 2>/dev/null || true
    )"

    CI_RELEASE_COUNT="$(
        grep -Eic \
            'release|publish|push' \
            "${CI_FILE}" 2>/dev/null || true
    )"
fi

log "CI_TEST_COUNT=${CI_TEST_COUNT}"
log "CI_BUILD_COUNT=${CI_BUILD_COUNT}"
log "CI_DEPLOY_COUNT=${CI_DEPLOY_COUNT}"
log "CI_RELEASE_COUNT=${CI_RELEASE_COUNT}"

if [ "${CI_TEST_COUNT}" -gt 0 ] &&
   [ "${CI_BUILD_COUNT}" -gt 0 ]; then
    pass "CI_VERIFICATION_BOUNDARY_PRESENT"
else
    review "CI_VERIFICATION_BOUNDARY_NOT_FULLY_DETECTED"
fi

if [ "${CI_DEPLOY_COUNT}" -eq 0 ] &&
   [ "${CI_RELEASE_COUNT}" -eq 0 ]; then
    pass "CI_HAS_NO_DIRECT_PRODUCTION_DEPLOYMENT_AUTHORITY"
else
    review "CI_CONTAINS_DEPLOYMENT_OR_RELEASE_SIGNAL"
fi

log ""
log "============================================================"
log "8. POST-DEPLOYMENT VERIFICATION DECISION"
log "============================================================"

POST_DEPLOY_VERIFICATION_AUTHORITY=0

if [ "${DEPLOY_VERIFY_COUNT}" -gt 0 ] &&
   [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then

    POST_DEPLOY_VERIFICATION_AUTHORITY=1
    pass "POST_DEPLOYMENT_VERIFICATION_AUTHORITY_ESTABLISHED"

elif [ "${COMPOSE_HEALTHCHECK_COUNT}" -gt 0 ] &&
     [ "${COMPOSE_HEALTHCHECK_TEST_COUNT}" -gt 0 ] &&
     [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then

    POST_DEPLOY_VERIFICATION_AUTHORITY=1
    pass "COMPOSE_HEALTHCHECK_PLUS_FAIL_FAST_PROVIDES_POST_DEPLOYMENT_SAFETY"

else

    review "POST_DEPLOYMENT_VERIFICATION_AUTHORITY_NOT_FULLY_ESTABLISHED"
fi

log "POST_DEPLOY_VERIFICATION_AUTHORITY=${POST_DEPLOY_VERIFICATION_AUTHORITY}"

log ""
log "============================================================"
log "9. ROLLBACK / RECOVERY AUTHORITY DECISION"
log "============================================================"

if [ "${DEPLOY_ROLLBACK_COUNT}" -gt 0 ]; then

    ROLLBACK_AUTHORITY=1
    pass "EXPLICIT_ROLLBACK_AUTHORITY_PRESENT"

elif [ "${DEPLOY_REVERT_COUNT}" -gt 0 ] &&
     [ "${DEPLOY_PREVIOUS_IMAGE_COUNT}" -gt 0 ]; then

    ROLLBACK_AUTHORITY=1
    pass "VERSION_REVERT_ROLLBACK_AUTHORITY_PRESENT"

elif [ "${DEPLOY_BACKUP_COUNT}" -gt 0 ] &&
     [ "${DEPLOY_REVERT_COUNT}" -gt 0 ]; then

    ROLLBACK_AUTHORITY=1
    pass "BACKUP_RESTORE_RECOVERY_AUTHORITY_PRESENT"

else

    ROLLBACK_AUTHORITY=0
    review "EXPLICIT_ROLLBACK_AUTHORITY_NOT_DETECTED"
fi

if [ "${ROLLBACK_AUTHORITY}" -gt 0 ]; then
    RECOVERY_AUTHORITY=1
    pass "RECOVERY_AUTHORITY_ESTABLISHED"
else
    review "RECOVERY_AUTHORITY_NOT_ESTABLISHED"
fi

log "ROLLBACK_AUTHORITY=${ROLLBACK_AUTHORITY}"
log "RECOVERY_AUTHORITY=${RECOVERY_AUTHORITY}"

log ""
log "============================================================"
log "10. DEPLOYMENT SAFETY GAP CLASSIFICATION"
log "============================================================"

DEPLOYMENT_SAFETY_GAP=0
DEPLOYMENT_SAFETY_BLOCKER=0

if [ "${POST_DEPLOY_VERIFICATION_AUTHORITY}" -eq 0 ]; then

    DEPLOYMENT_SAFETY_GAP=1
    review "POST_DEPLOYMENT_VERIFICATION_GAP"

fi

if [ "${ROLLBACK_AUTHORITY}" -eq 0 ]; then

    DEPLOYMENT_SAFETY_GAP=1
    review "ROLLBACK_RECOVERY_GAP"

fi

if [ "${DEPLOY_FAIL_FAST_COUNT}" -eq 0 ] ||
   [ "${DEPLOY_COMPOSE_COUNT}" -eq 0 ]; then

    DEPLOYMENT_SAFETY_BLOCKER=1
    fail "DEPLOYMENT_EXECUTION_SAFETY_BASELINE_INCOMPLETE"

fi

if [ "${COMPOSE_HEALTHCHECK_COUNT}" -eq 0 ] ||
   [ "${COMPOSE_HEALTHCHECK_TEST_COUNT}" -eq 0 ]; then

    DEPLOYMENT_SAFETY_BLOCKER=1
    fail "COMPOSE_HEALTHCHECK_BASELINE_INCOMPLETE"

fi

log "DEPLOYMENT_SAFETY_GAP=${DEPLOYMENT_SAFETY_GAP}"
log "DEPLOYMENT_SAFETY_BLOCKER=${DEPLOYMENT_SAFETY_BLOCKER}"

log ""
log "============================================================"
log "11. R50 ARCHITECTURAL BOUNDARY CONFIRMATION"
log "============================================================"

if [ "${R50_ARCHITECTURAL_SEPARATION}" -eq 1 ] &&
   [ "${R50_PRODUCTION_DEPLOYMENT_AUTHORITY}" -eq 1 ] &&
   [ "${R50_PRODUCTION_DEPLOYMENT_GAP}" -eq 0 ] &&
   [ "${R50_PRODUCTION_DEPLOYMENT_BLOCKER}" -eq 0 ]; then

    pass "R50_PRODUCTION_DEPLOYMENT_BOUNDARY_REMAINS_VALID"

else

    review "R50_PRODUCTION_DEPLOYMENT_BOUNDARY_NOT_FULLY_CONFIRMED"

fi

log ""
log "============================================================"
log "12. FINAL R51 DECISION"
log "============================================================"

log "POST_DEPLOY_VERIFICATION_AUTHORITY=${POST_DEPLOY_VERIFICATION_AUTHORITY}"
log "FAIL_CLOSED_DEPLOYMENT_AUTHORITY=${FAIL_CLOSED_DEPLOYMENT_AUTHORITY}"
log "ROLLBACK_AUTHORITY=${ROLLBACK_AUTHORITY}"
log "RECOVERY_AUTHORITY=${RECOVERY_AUTHORITY}"
log "DEPLOYMENT_SAFETY_GAP=${DEPLOYMENT_SAFETY_GAP}"
log "DEPLOYMENT_SAFETY_BLOCKER=${DEPLOYMENT_SAFETY_BLOCKER}"

log "DEPLOY_FAIL_FAST_COUNT=${DEPLOY_FAIL_FAST_COUNT}"
log "DEPLOY_COMPOSE_COUNT=${DEPLOY_COMPOSE_COUNT}"
log "DEPLOY_VERIFY_COUNT=${DEPLOY_VERIFY_COUNT}"
log "DEPLOY_HEALTH_COUNT=${DEPLOY_HEALTH_COUNT}"
log "DEPLOY_READINESS_COUNT=${DEPLOY_READINESS_COUNT}"
log "DEPLOY_STATUS_COUNT=${DEPLOY_STATUS_COUNT}"
log "DEPLOY_EXIT_CODE_CHECK_COUNT=${DEPLOY_EXIT_CODE_CHECK_COUNT}"
log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
log "DEPLOY_REVERT_COUNT=${DEPLOY_REVERT_COUNT}"
log "DEPLOY_BACKUP_COUNT=${DEPLOY_BACKUP_COUNT}"

log "COMPOSE_HEALTHCHECK_COUNT=${COMPOSE_HEALTHCHECK_COUNT}"
log "COMPOSE_HEALTHCHECK_TEST_COUNT=${COMPOSE_HEALTHCHECK_TEST_COUNT}"
log "COMPOSE_DEPENDS_ON_COUNT=${COMPOSE_DEPENDS_ON_COUNT}"
log "COMPOSE_RESTART_COUNT=${COMPOSE_RESTART_COUNT}"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

if [ "${DEPLOYMENT_SAFETY_BLOCKER}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R51_PRODUCTION_DEPLOYMENT_SAFETY_BLOCKER_CONFIRMED"
    EXIT_CODE=2

elif [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R51_PRODUCTION_DEPLOYMENT_SAFETY_GATE_FAILED"
    EXIT_CODE=2

elif [ "${DEPLOYMENT_SAFETY_GAP}" -eq 0 ] &&
     [ "${POST_DEPLOY_VERIFICATION_AUTHORITY}" -eq 1 ] &&
     [ "${ROLLBACK_AUTHORITY}" -eq 1 ]; then

    STATUS="PASS"
    RESULT="P0_03_R51_PRODUCTION_DEPLOYMENT_SAFETY_AUTHORITY_CLOSED"
    EXIT_CODE=0

else

    STATUS="REVIEW"
    RESULT="P0_03_R51_PRODUCTION_DEPLOYMENT_SAFETY_AUTHORITY_REVIEW"
    EXIT_CODE=1
fi

log "P0_03_R51_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"

log ""
log "============================================================"
log "R51 COMPLETE"
log "============================================================"

exit "${EXIT_CODE}"
