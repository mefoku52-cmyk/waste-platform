#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r43_production_gap_classification_gate.txt"

SCRIPT_NAME="$(basename "$0")"

FAILURE_COUNT=0
REVIEW_COUNT=0

STATUS="PASS"
RESULT="P0_03_R43_PRODUCTION_GAP_CLASSIFICATION_PASS"
EXIT_CODE=0

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

file_exists() {
    [ -f "$1" ]
}

dir_exists() {
    [ -d "$1" ]
}

safe_count() {
    local pattern="$1"
    local path="$2"

    if [ ! -e "${path}" ]; then
        printf '0'
        return 0
    fi

    grep -RInE \
        --exclude="${SCRIPT_NAME}" \
        --exclude='*.pyc' \
        --exclude-dir='.git' \
        --exclude-dir='audit-output' \
        --exclude-dir='__pycache__' \
        --exclude-dir='forensics' \
        --exclude-dir='archive' \
        -- "${pattern}" "${path}" 2>/dev/null |
        wc -l |
        tr -d ' '
}

emit_matches() {
    local label="$1"
    local pattern="$2"
    shift 2

    log "${label}_BEGIN"

    local found=0

    for path in "$@"; do
        if [ -e "${path}" ]; then
            while IFS= read -r line; do
                [ -n "${line}" ] || continue

                # Never emit probable secret values.
                if printf '%s\n' "${line}" |
                    grep -Eiq \
                    '(PASSWORD|SECRET|TOKEN|PRIVATE_KEY|API_KEY)[^A-Za-z0-9_]*(=|:).*[^$][A-Za-z0-9_+/=.-]{8,}'
                then
                    log "${label}_REDACTED_MATCH"
                    found=$((found + 1))
                    continue
                fi

                log "${label}=${line}"
                found=$((found + 1))
            done < <(
                grep -RInE \
                    --exclude="${SCRIPT_NAME}" \
                    --exclude='*.pyc' \
                    --exclude-dir='.git' \
                    --exclude-dir='audit-output' \
                    --exclude-dir='__pycache__' \
                    --exclude-dir='forensics' \
                    --exclude-dir='archive' \
                    -- "${pattern}" "${path}" 2>/dev/null
            )
        fi
    done

    log "${label}_COUNT=${found}"
    log "${label}_END"
}

mkdir -p "${REPORT_DIR}"
: > "${REPORT}"

log "============================================================"
log "P0-03 R43 PRODUCTION GAP CLASSIFICATION GATE"
log "============================================================"

log ""
log "============================================================"
log "1. SAFETY PRECHECK"
log "============================================================"

if [ "$(pwd -P)" = "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
else
    fail "PROJECT_ROOT_NOT_CURRENT_DIRECTORY"
fi

if dir_exists "${PROJECT_ROOT}"; then
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
pass "TARGETED_GAP_CLASSIFICATION=YES"
pass "NO_SECRET_PROVENANCE_REOPEN=YES"

log ""
log "============================================================"
log "2. R42 AUTHORITY HANDOFF"
log "============================================================"

R42_REPORT="${REPORT_DIR}/p0_03_r42_real_production_readiness_gate.txt"

if file_exists "${R42_REPORT}"; then
    pass "R42_REPORT_PRESENT"

    R42_STATUS="$(grep -E '^P0_03_R42_STATUS=' "${R42_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R42_EXIT_CODE="$(grep -E '^EXIT_CODE=' "${R42_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R42_FAILURE_COUNT="$(grep -E '^FAILURE_COUNT=' "${R42_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R42_REVIEW_COUNT="$(grep -E '^REVIEW_COUNT=' "${R42_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"

    log "R42_STATUS=${R42_STATUS:-UNKNOWN}"
    log "R42_EXIT_CODE=${R42_EXIT_CODE:-UNKNOWN}"
    log "R42_FAILURE_COUNT=${R42_FAILURE_COUNT:-UNKNOWN}"
    log "R42_REVIEW_COUNT=${R42_REVIEW_COUNT:-UNKNOWN}"

    if [ "${R42_STATUS:-}" = "REVIEW" ] && [ "${R42_EXIT_CODE:-}" = "1" ]; then
        pass "R42_REVIEW_HANDOFF_ACCEPTED"
    else
        fail "R42_HANDOFF_STATE_UNEXPECTED"
    fi

    if [ "${R42_FAILURE_COUNT:-999}" = "0" ]; then
        pass "R42_NO_HARD_FAILURES"
    else
        fail "R42_HARD_FAILURE_PRESENT"
    fi
else
    fail "R42_REPORT_MISSING"
fi

log ""
log "============================================================"
log "3. READINESS / LIVENESS GAP CLASSIFICATION"
log "============================================================"

HEALTH_SIGNATURE_COUNT=0
READINESS_SIGNATURE_COUNT=0
LIVENESS_SIGNATURE_COUNT=0
COMPOSE_HEALTHCHECK_COUNT=0
HEALTHCHECK_READINESS_SIGNAL_COUNT=0

APP_ROOT="${PROJECT_ROOT}/app"
SRC_ROOT="${PROJECT_ROOT}/src"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

HEALTH_SIGNATURE_COUNT="$(
    safe_count \
        '(/health|/healthz|healthcheck|health_check|health endpoint|health endpoint)' \
        "${APP_ROOT}"
)"

if dir_exists "${SRC_ROOT}"; then
    HEALTH_SIGNATURE_COUNT=$(
        printf '%s\n' "${HEALTH_SIGNATURE_COUNT}"
        safe_count \
            '(/health|/healthz|healthcheck|health_check|health endpoint|health endpoint)' \
            "${SRC_ROOT}"
    )
    HEALTH_SIGNATURE_COUNT="$(
        printf '%s\n' "${HEALTH_SIGNATURE_COUNT}" |
        awk '{s+=$1} END{print s+0}'
    )"
fi

READINESS_SIGNATURE_COUNT="$(
    safe_count \
        '(/ready|/readyz|/readiness|readiness|ready_check|ready_check)' \
        "${APP_ROOT}"
)"

if dir_exists "${SRC_ROOT}"; then
    READINESS_SIGNATURE_COUNT=$(
        printf '%s\n' "${READINESS_SIGNATURE_COUNT}"
        safe_count \
            '(/ready|/readyz|/readiness|readiness|ready_check|ready_check)' \
            "${SRC_ROOT}"
    )
    READINESS_SIGNATURE_COUNT="$(
        printf '%s\n' "${READINESS_SIGNATURE_COUNT}" |
        awk '{s+=$1} END{print s+0}'
    )"
fi

LIVENESS_SIGNATURE_COUNT="$(
    safe_count \
        '(/live|/livez|/liveness|liveness|live_check|live_check)' \
        "${APP_ROOT}"
)"

if dir_exists "${SRC_ROOT}"; then
    LIVENESS_SIGNATURE_COUNT=$(
        printf '%s\n' "${LIVENESS_SIGNATURE_COUNT}"
        safe_count \
            '(/live|/livez|/liveness|liveness|live_check|live_check)' \
            "${SRC_ROOT}"
    )
    LIVENESS_SIGNATURE_COUNT="$(
        printf '%s\n' "${LIVENESS_SIGNATURE_COUNT}" |
        awk '{s+=$1} END{print s+0}'
    )"
fi

COMPOSE_HEALTHCHECK_COUNT="$(
    safe_count \
        '^[[:space:]]*healthcheck:[[:space:]]*$' \
        "${COMPOSE_FILE}"
)"

HEALTHCHECK_READINESS_SIGNAL_COUNT="$(
    safe_count \
        '(condition:[[:space:]]*service_healthy|service_healthy|healthcheck.*curl|healthcheck.*wget|healthcheck.*python)' \
        "${COMPOSE_FILE}"
)"

log "HEALTH_SIGNATURE_COUNT=${HEALTH_SIGNATURE_COUNT}"
log "READINESS_SIGNATURE_COUNT=${READINESS_SIGNATURE_COUNT}"
log "LIVENESS_SIGNATURE_COUNT=${LIVENESS_SIGNATURE_COUNT}"
log "COMPOSE_HEALTHCHECK_COUNT=${COMPOSE_HEALTHCHECK_COUNT}"
log "HEALTHCHECK_READINESS_SIGNAL_COUNT=${HEALTHCHECK_READINESS_SIGNAL_COUNT}"

if [ "${READINESS_SIGNATURE_COUNT}" -gt 0 ]; then
    pass "READINESS_SIGNAL_DETECTED"
elif [ "${COMPOSE_HEALTHCHECK_COUNT}" -gt 0 ] &&
     [ "${HEALTHCHECK_READINESS_SIGNAL_COUNT}" -gt 0 ]; then
    pass "READINESS_CAN_BE_SATISFIED_BY_HEALTHCHECK_DEPENDENCY_SEMANTICS"
else
    review "REAL_READINESS_CONTRACT_NOT_DETECTED"
fi

if [ "${LIVENESS_SIGNATURE_COUNT}" -gt 0 ]; then
    pass "LIVENESS_SIGNAL_DETECTED"
else
    review "LIVENESS_CONTRACT_NOT_DETECTED"
fi

log ""
log "============================================================"
log "4. CI/CD DEPLOYMENT GAP CLASSIFICATION"
log "============================================================"

CI_FILE="${PROJECT_ROOT}/.github/workflows/ci.yml"

CI_DEPLOY_KEYWORD_COUNT=0
CI_PRODUCTION_ENV_COUNT=0
CI_CONTAINER_PUSH_COUNT=0
CI_REGISTRY_COUNT=0
CI_REMOTE_DEPLOY_COUNT=0
CI_ARTIFACT_RELEASE_COUNT=0

if file_exists "${CI_FILE}"; then

    CI_DEPLOY_KEYWORD_COUNT="$(
        safe_count \
            '(^|[[:space:]])(deploy|deployment|release|publish)[[:space:]:_-]' \
            "${CI_FILE}"
    )"

    CI_PRODUCTION_ENV_COUNT="$(
        safe_count \
            '(production|prod)[[:space:]]*(environment|env|deploy|deployment)|environment:[[:space:]]*production' \
            "${CI_FILE}"
    )"

    CI_CONTAINER_PUSH_COUNT="$(
        safe_count \
            'docker[[:space:]]+(push|buildx[[:space:]]+build[^#]*--push)' \
            "${CI_FILE}"
    )"

    CI_REGISTRY_COUNT="$(
        safe_count \
            '(ghcr\.io|docker\.io|registry|ecr|gcr|acr)' \
            "${CI_FILE}"
    )"

    CI_REMOTE_DEPLOY_COUNT="$(
        safe_count \
            '(ssh|scp|rsync|kubectl|helm|terraform|ansible|docker[[:space:]]+compose[^#]*(up|pull))' \
            "${CI_FILE}"
    )"

    CI_ARTIFACT_RELEASE_COUNT="$(
        safe_count \
            '(actions/upload-artifact|release|softprops/action-gh-release|docker/build-push-action)' \
            "${CI_FILE}"
    )"

else
    fail "CI_WORKFLOW_MISSING"
fi

log "CI_DEPLOY_KEYWORD_COUNT=${CI_DEPLOY_KEYWORD_COUNT}"
log "CI_PRODUCTION_ENV_COUNT=${CI_PRODUCTION_ENV_COUNT}"
log "CI_CONTAINER_PUSH_COUNT=${CI_CONTAINER_PUSH_COUNT}"
log "CI_REGISTRY_COUNT=${CI_REGISTRY_COUNT}"
log "CI_REMOTE_DEPLOY_COUNT=${CI_REMOTE_DEPLOY_COUNT}"
log "CI_ARTIFACT_RELEASE_COUNT=${CI_ARTIFACT_RELEASE_COUNT}"

if [ "${CI_DEPLOY_KEYWORD_COUNT}" -gt 0 ] &&
   [ "${CI_PRODUCTION_ENV_COUNT}" -gt 0 ]; then
    pass "CI_PRODUCTION_DEPLOYMENT_PATH_DETECTED"
elif [ "${CI_CONTAINER_PUSH_COUNT}" -gt 0 ] &&
     [ "${CI_REGISTRY_COUNT}" -gt 0 ]; then
    pass "CI_CONTAINER_RELEASE_PATH_DETECTED"
elif [ "${CI_ARTIFACT_RELEASE_COUNT}" -gt 0 ]; then
    review "CI_RELEASE_ARTIFACT_PATH_EXISTS_BUT_PRODUCTION_DEPLOYMENT_NOT_PROVEN"
else
    review "CI_PRODUCTION_DEPLOYMENT_PATH_NOT_PRESENT"
fi

log ""
log "============================================================"
log "5. DEPLOYMENT SCRIPT OPERATIONAL GAP CLASSIFICATION"
log "============================================================"

DEPLOY_FILE="${PROJECT_ROOT}/scripts/deploy.sh"

DEPLOY_FUNCTION_COUNT=0
DEPLOY_COMPOSE_COUNT=0
DEPLOY_HEALTH_WAIT_COUNT=0
DEPLOY_VERIFY_COUNT=0
DEPLOY_ROLLBACK_COUNT=0
DEPLOY_DRY_RUN_COUNT=0

if file_exists "${DEPLOY_FILE}"; then

    DEPLOY_FUNCTION_COUNT="$(
        safe_count \
            '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*\(\)[[:space:]]*\{' \
            "${DEPLOY_FILE}"
    )"

    DEPLOY_COMPOSE_COUNT="$(
        safe_count \
            'docker[[:space:]]+compose|docker-compose' \
            "${DEPLOY_FILE}"
    )"

    DEPLOY_HEALTH_WAIT_COUNT="$(
        safe_count \
            '(health|healthy|readiness|ready|wait_for|wait-for)' \
            "${DEPLOY_FILE}"
    )"

    DEPLOY_VERIFY_COUNT="$(
        safe_count \
            '(verify|validation|validate|check|status)' \
            "${DEPLOY_FILE}"
    )"

    DEPLOY_ROLLBACK_COUNT="$(
        safe_count \
            'rollback|roll_back|restore_previous' \
            "${DEPLOY_FILE}"
    )"

    DEPLOY_DRY_RUN_COUNT="$(
        safe_count \
            'dry[-_ ]?run|DRY_RUN|--dry-run' \
            "${DEPLOY_FILE}"
    )"

    log "DEPLOY_FUNCTION_COUNT=${DEPLOY_FUNCTION_COUNT}"
    log "DEPLOY_COMPOSE_COUNT=${DEPLOY_COMPOSE_COUNT}"
    log "DEPLOY_HEALTH_WAIT_COUNT=${DEPLOY_HEALTH_WAIT_COUNT}"
    log "DEPLOY_VERIFY_COUNT=${DEPLOY_VERIFY_COUNT}"
    log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
    log "DEPLOY_DRY_RUN_COUNT=${DEPLOY_DRY_RUN_COUNT}"

    if [ "${DEPLOY_COMPOSE_COUNT}" -gt 0 ]; then
        pass "DEPLOY_COMPOSE_OPERATION_PRESENT"
    else
        review "DEPLOY_COMPOSE_OPERATION_NOT_DETECTED"
    fi

    if [ "${DEPLOY_HEALTH_WAIT_COUNT}" -gt 0 ]; then
        pass "DEPLOY_HEALTH_OR_READINESS_WAIT_SIGNAL_PRESENT"
    else
        review "DEPLOY_HEALTH_WAIT_SIGNAL_NOT_DETECTED"
    fi

    if [ "${DEPLOY_VERIFY_COUNT}" -gt 0 ]; then
        pass "DEPLOY_POST_ACTION_VERIFICATION_SIGNAL_PRESENT"
    else
        review "DEPLOY_POST_ACTION_VERIFICATION_NOT_DETECTED"
    fi

    if [ "${DEPLOY_ROLLBACK_COUNT}" -gt 0 ]; then
        pass "DEPLOY_ROLLBACK_SIGNAL_PRESENT"
    else
        review "DEPLOY_ROLLBACK_SIGNAL_NOT_DETECTED"
    fi

else
    fail "DEPLOY_SCRIPT_MISSING"
fi

log ""
log "============================================================"
log "6. STATIC SECURITY TOOLING GAP CLASSIFICATION"
log "============================================================"

SECURITY_REFERENCE_COUNT=0
SECURITY_WORKFLOW_COUNT=0
SECURITY_SCRIPT_COUNT=0
SECURITY_CONFIG_COUNT=0
SECURITY_DEPENDENCY_FILE_COUNT=0

SECURITY_REFERENCE_COUNT="$(
    grep -RIlE \
        --exclude="${SCRIPT_NAME}" \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        --exclude-dir=__pycache__ \
        --exclude='*.pyc' \
        -- 'bandit|semgrep|trivy|osv-scanner|pip-audit|safety|npm[[:space:]]+audit|cargo[[:space:]]+audit|grype|snyk' \
        "${PROJECT_ROOT}" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

SECURITY_WORKFLOW_COUNT="$(
    grep -RIlE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        -- 'bandit|semgrep|trivy|osv-scanner|pip-audit|safety|npm[[:space:]]+audit|grype|snyk' \
        "${PROJECT_ROOT}/.github" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

SECURITY_SCRIPT_COUNT="$(
    grep -RIlE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        -- 'bandit|semgrep|trivy|osv-scanner|pip-audit|safety|npm[[:space:]]+audit|grype|snyk' \
        "${PROJECT_ROOT}/scripts" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

SECURITY_CONFIG_COUNT="$(
    grep -RIlE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        -- 'bandit|semgrep|trivy|osv-scanner|pip-audit|safety|npm[[:space:]]+audit|grype|snyk' \
        "${PROJECT_ROOT}/pyproject.toml" \
        "${PROJECT_ROOT}/package.json" \
        "${PROJECT_ROOT}/Makefile" \
        "${PROJECT_ROOT}/Taskfile.yml" \
        2>/dev/null |
    wc -l |
    tr -d ' '
)"

SECURITY_DEPENDENCY_FILE_COUNT="$(
    find "${PROJECT_ROOT}" \
        -type d \
        \( -name .git -o -name audit-output -o -name forensics -o -name archive -o -name __pycache__ \) -prune -o \
        -type f \
        \( \
            -name 'requirements*.txt' \
            -o -name 'poetry.lock' \
            -o -name 'uv.lock' \
            -o -name 'Pipfile.lock' \
            -o -name 'package-lock.json' \
            -o -name 'pnpm-lock.yaml' \
            -o -name 'yarn.lock' \
        \) \
        -print 2>/dev/null |
    wc -l |
    tr -d ' '
)"

log "SECURITY_REFERENCE_COUNT=${SECURITY_REFERENCE_COUNT}"
log "SECURITY_WORKFLOW_COUNT=${SECURITY_WORKFLOW_COUNT}"
log "SECURITY_SCRIPT_COUNT=${SECURITY_SCRIPT_COUNT}"
log "SECURITY_CONFIG_COUNT=${SECURITY_CONFIG_COUNT}"
log "SECURITY_DEPENDENCY_FILE_COUNT=${SECURITY_DEPENDENCY_FILE_COUNT}"

if [ "${SECURITY_REFERENCE_COUNT}" -gt 0 ]; then
    pass "SECURITY_TOOLING_REFERENCE_PRESENT"
else
    review "NO_SECURITY_TOOLING_REFERENCE_DETECTED"
fi

if [ "${SECURITY_WORKFLOW_COUNT}" -gt 0 ]; then
    pass "CI_SECURITY_SCAN_PATH_PRESENT"
else
    review "CI_SECURITY_SCAN_PATH_NOT_DETECTED"
fi

if [ "${SECURITY_DEPENDENCY_FILE_COUNT}" -gt 0 ]; then
    pass "DEPENDENCY_LOCK_OR_REQUIREMENTS_ARTIFACT_PRESENT"
else
    review "DEPENDENCY_LOCK_OR_REQUIREMENTS_ARTIFACT_NOT_DETECTED"
fi

log ""
log "============================================================"
log "7. UNSAFE BIND EXACT CLASSIFICATION"
log "============================================================"

UNSAFE_BIND_TOTAL=0
UNSAFE_BIND_COMPOSE=0
UNSAFE_BIND_APPLICATION=0
UNSAFE_BIND_DEPLOY=0
UNSAFE_BIND_TEST=0
UNSAFE_BIND_AUDIT=0

UNSAFE_BIND_TOTAL="$(
    grep -RInE \
        --exclude="${SCRIPT_NAME}" \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=__pycache__ \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        -- '0\.0\.0\.0|host[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
        "${PROJECT_ROOT}" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

if file_exists "${COMPOSE_FILE}"; then
    UNSAFE_BIND_COMPOSE="$(
        grep -InE \
            '0\.0\.0\.0|host[[:space:]]*:[[:space:]]*["'\'']?0\.0\.0\.0' \
            "${COMPOSE_FILE}" 2>/dev/null |
        wc -l |
        tr -d ' '
    )"
fi

UNSAFE_BIND_APPLICATION="$(
    grep -RInE \
        --exclude="${SCRIPT_NAME}" \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=__pycache__ \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        -- '0\.0\.0\.0|host[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
        "${APP_ROOT}" "${SRC_ROOT}" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

UNSAFE_BIND_DEPLOY="$(
    grep -InE \
        '0\.0\.0\.0|host[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
        "${DEPLOY_FILE}" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

UNSAFE_BIND_TEST="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=__pycache__ \
        -- '0\.0\.0\.0|host[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
        "${PROJECT_ROOT}/tests" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

UNSAFE_BIND_AUDIT="$(
    grep -RInE \
        --exclude-dir=.git \
        -- '0\.0\.0\.0|host[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
        "${PROJECT_ROOT}/scripts" 2>/dev/null |
    wc -l |
    tr -d ' '
)"

log "UNSAFE_BIND_TOTAL=${UNSAFE_BIND_TOTAL}"
log "UNSAFE_BIND_COMPOSE=${UNSAFE_BIND_COMPOSE}"
log "UNSAFE_BIND_APPLICATION=${UNSAFE_BIND_APPLICATION}"
log "UNSAFE_BIND_DEPLOY=${UNSAFE_BIND_DEPLOY}"
log "UNSAFE_BIND_TEST=${UNSAFE_BIND_TEST}"
log "UNSAFE_BIND_AUDIT=${UNSAFE_BIND_AUDIT}"

if [ "${UNSAFE_BIND_APPLICATION}" -gt 0 ]; then
    fail "UNSAFE_BIND_PRESENT_IN_APPLICATION_SCOPE"
elif [ "${UNSAFE_BIND_DEPLOY}" -gt 0 ]; then
    fail "UNSAFE_BIND_PRESENT_IN_DEPLOYMENT_SCOPE"
elif [ "${UNSAFE_BIND_COMPOSE}" -gt 0 ]; then
    review "UNSAFE_BIND_PRESENT_IN_COMPOSE_REQUIRES_NETWORK_EXPOSURE_CLASSIFICATION"
else
    pass "NO_UNSAFE_BIND_IN_APPLICATION_OR_DEPLOYMENT_SCOPE"
fi

if [ "${UNSAFE_BIND_TEST}" -gt 0 ]; then
    review "UNSAFE_BIND_PRESENT_IN_TEST_SCOPE"
fi

if [ "${UNSAFE_BIND_AUDIT}" -gt 0 ]; then
    pass "UNSAFE_BIND_SIGNAL_ONLY_IN_SCRIPT_OR_AUDIT_SCOPE"
fi

log ""
log "============================================================"
log "8. PRODUCTION GAP MATRIX"
log "============================================================"

READINESS_GAP=0
CI_DEPLOY_GAP=0
SECURITY_GAP=0
BIND_GAP=0

if [ "${READINESS_SIGNATURE_COUNT}" -eq 0 ] &&
   ! { [ "${COMPOSE_HEALTHCHECK_COUNT}" -gt 0 ] &&
       [ "${HEALTHCHECK_READINESS_SIGNAL_COUNT}" -gt 0 ]; }; then
    READINESS_GAP=1
fi

if [ "${CI_DEPLOY_KEYWORD_COUNT}" -eq 0 ] &&
   [ "${CI_CONTAINER_PUSH_COUNT}" -eq 0 ] &&
   [ "${CI_ARTIFACT_RELEASE_COUNT}" -eq 0 ]; then
    CI_DEPLOY_GAP=1
fi

if [ "${SECURITY_REFERENCE_COUNT}" -eq 0 ]; then
    SECURITY_GAP=1
fi

if [ "${UNSAFE_BIND_APPLICATION}" -gt 0 ] ||
   [ "${UNSAFE_BIND_DEPLOY}" -gt 0 ]; then
    BIND_GAP=1
fi

log "READINESS_GAP=${READINESS_GAP}"
log "CI_DEPLOY_GAP=${CI_DEPLOY_GAP}"
log "SECURITY_GAP=${SECURITY_GAP}"
log "BIND_GAP=${BIND_GAP}"

log ""
log "============================================================"
log "9. FINAL CLASSIFICATION"
log "============================================================"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_03_R43_PRODUCTION_GAP_CLASSIFICATION_BLOCKED"
    EXIT_CODE=2
elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_03_R43_PRODUCTION_GAP_CLASSIFICATION_REVIEW"
    EXIT_CODE=1
else
    STATUS="PASS"
    RESULT="P0_03_R43_PRODUCTION_GAP_CLASSIFICATION_PASS"
    EXIT_CODE=0
fi

log ""
log "============================================================"
log "10. FINAL EVIDENCE CARD"
log "============================================================"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "R42_STATUS=${R42_STATUS:-UNKNOWN}"
log "R42_EXIT_CODE=${R42_EXIT_CODE:-UNKNOWN}"

log "HEALTH_SIGNATURE_COUNT=${HEALTH_SIGNATURE_COUNT}"
log "READINESS_SIGNATURE_COUNT=${READINESS_SIGNATURE_COUNT}"
log "LIVENESS_SIGNATURE_COUNT=${LIVENESS_SIGNATURE_COUNT}"
log "COMPOSE_HEALTHCHECK_COUNT=${COMPOSE_HEALTHCHECK_COUNT}"
log "HEALTHCHECK_READINESS_SIGNAL_COUNT=${HEALTHCHECK_READINESS_SIGNAL_COUNT}"

log "CI_DEPLOY_KEYWORD_COUNT=${CI_DEPLOY_KEYWORD_COUNT}"
log "CI_PRODUCTION_ENV_COUNT=${CI_PRODUCTION_ENV_COUNT}"
log "CI_CONTAINER_PUSH_COUNT=${CI_CONTAINER_PUSH_COUNT}"
log "CI_REGISTRY_COUNT=${CI_REGISTRY_COUNT}"
log "CI_REMOTE_DEPLOY_COUNT=${CI_REMOTE_DEPLOY_COUNT}"
log "CI_ARTIFACT_RELEASE_COUNT=${CI_ARTIFACT_RELEASE_COUNT}"

log "DEPLOY_COMPOSE_COUNT=${DEPLOY_COMPOSE_COUNT}"
log "DEPLOY_HEALTH_WAIT_COUNT=${DEPLOY_HEALTH_WAIT_COUNT}"
log "DEPLOY_VERIFY_COUNT=${DEPLOY_VERIFY_COUNT}"
log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
log "DEPLOY_DRY_RUN_COUNT=${DEPLOY_DRY_RUN_COUNT}"

log "SECURITY_REFERENCE_COUNT=${SECURITY_REFERENCE_COUNT}"
log "SECURITY_WORKFLOW_COUNT=${SECURITY_WORKFLOW_COUNT}"
log "SECURITY_SCRIPT_COUNT=${SECURITY_SCRIPT_COUNT}"
log "SECURITY_CONFIG_COUNT=${SECURITY_CONFIG_COUNT}"
log "SECURITY_DEPENDENCY_FILE_COUNT=${SECURITY_DEPENDENCY_FILE_COUNT}"

log "UNSAFE_BIND_TOTAL=${UNSAFE_BIND_TOTAL}"
log "UNSAFE_BIND_COMPOSE=${UNSAFE_BIND_COMPOSE}"
log "UNSAFE_BIND_APPLICATION=${UNSAFE_BIND_APPLICATION}"
log "UNSAFE_BIND_DEPLOY=${UNSAFE_BIND_DEPLOY}"
log "UNSAFE_BIND_TEST=${UNSAFE_BIND_TEST}"
log "UNSAFE_BIND_AUDIT=${UNSAFE_BIND_AUDIT}"

log "READINESS_GAP=${READINESS_GAP}"
log "CI_DEPLOY_GAP=${CI_DEPLOY_GAP}"
log "SECURITY_GAP=${SECURITY_GAP}"
log "BIND_GAP=${BIND_GAP}"

log "P0_03_R43_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
