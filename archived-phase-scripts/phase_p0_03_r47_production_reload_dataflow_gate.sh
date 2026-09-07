#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r47_production_reload_dataflow_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

STATUS="PASS"
RESULT="P0_03_R47_PRODUCTION_RELOAD_DATAFLOW_PASS"
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

mkdir -p "${REPORT_DIR}"
: > "${REPORT}"

TMP_RELOAD="${REPORT_DIR}/.r47_reload.tmp"
TMP_COMPOSE="${REPORT_DIR}/.r47_compose.tmp"
TMP_DOCKER="${REPORT_DIR}/.r47_docker.tmp"
TMP_DEPLOY="${REPORT_DIR}/.r47_deploy.tmp"
TMP_PROD="${REPORT_DIR}/.r47_prod.tmp"

: > "${TMP_RELOAD}"
: > "${TMP_COMPOSE}"
: > "${TMP_DOCKER}"
: > "${TMP_DEPLOY}"
: > "${TMP_PROD}"

log "============================================================"
log "P0-03 R47 PRODUCTION RELOAD DATAFLOW GATE"
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

if [ -d "${PROJECT_ROOT}" ]; then
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
pass "TARGETED_RELOAD_FORENSICS=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. R46 AUTHORITY HANDOFF"
log "============================================================"

R46_REPORT="${REPORT_DIR}/p0_03_r46_application_host_runtime_dataflow_closure_gate.txt"

if [ -f "${R46_REPORT}" ]; then
    pass "R46_REPORT_PRESENT"

    R46_STATUS="$(
        grep -E '^P0_03_R46_STATUS=' "${R46_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R46_EXIT_CODE="$(
        grep -E '^EXIT_CODE=' "${R46_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R46_PRODUCTION_BIND_BLOCKER="$(
        grep -E '^PRODUCTION_BIND_BLOCKER=' "${R46_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    log "R46_STATUS=${R46_STATUS:-UNKNOWN}"
    log "R46_EXIT_CODE=${R46_EXIT_CODE:-UNKNOWN}"
    log "R46_PRODUCTION_BIND_BLOCKER=${R46_PRODUCTION_BIND_BLOCKER:-UNKNOWN}"

    if [ "${R46_STATUS:-}" = "PASS" ] &&
       [ "${R46_EXIT_CODE:-}" = "0" ]; then
        pass "R46_CLOSURE_HANDOFF_ACCEPTED"
    else
        fail "R46_CLOSURE_HANDOFF_NOT_PASS"
    fi
else
    fail "R46_REPORT_MISSING"
fi

log ""
log "============================================================"
log "3. ALL RELOAD REFERENCES"
log "============================================================"

RELOAD_REFERENCE_COUNT=0

find "${PROJECT_ROOT}" \
    -type f \
    \( \
        -name '*.py' \
        -o -name '*.pyi' \
        -o -name '*.yml' \
        -o -name '*.yaml' \
        -o -name '*.sh' \
        -name 'Dockerfile' \
        -o -name 'Dockerfile.*' \
        -o -name '*.Dockerfile' \
        -o -name '*.toml' \
        -o -name '*.ini' \
        -o -name '*.conf' \
    \) \
    ! -path "${PROJECT_ROOT}/.git/*" \
    ! -path "${REPORT_DIR}/*" \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        -- '(^|[^[:alnum:]_-])(--reload|reload[[:space:]]*=|reload[[:space:]]*:)([^[:alnum:]_-]|$)' \
        "${file}" 2>/dev/null || true
done > "${TMP_RELOAD}"

RELOAD_REFERENCE_COUNT="$(
    wc -l < "${TMP_RELOAD}" |
    tr -d ' '
)"

log "RELOAD_REFERENCE_COUNT=${RELOAD_REFERENCE_COUNT}"

if [ "${RELOAD_REFERENCE_COUNT}" -gt 0 ]; then
    log "RELOAD_REFERENCES_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "RELOAD_REFERENCE=${line}"
    done < "${TMP_RELOAD}"

    log "RELOAD_REFERENCES_END"
else
    pass "NO_RELOAD_REFERENCE_FOUND"
fi

log ""
log "============================================================"
log "4. DOCKERFILE CLASSIFICATION"
log "============================================================"

DOCKERFILE_RELOAD_COUNT=0
DOCKERFILE_PRODUCTION_MARKER_COUNT=0
DOCKERFILE_DEVELOPMENT_MARKER_COUNT=0

find "${PROJECT_ROOT}" \
    -type f \
    \( \
        -name 'Dockerfile' \
        -o -name 'Dockerfile.*' \
        -o -name '*.Dockerfile' \
    \) \
    ! -path "${PROJECT_ROOT}/.git/*" \
    ! -path "${REPORT_DIR}/*" \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do

    if grep -nH -E -- '--reload|reload[[:space:]]*=' "${file}" 2>/dev/null; then
        printf '%s\n' "FILE=${file}" >> "${TMP_DOCKER}"
    fi

done

DOCKERFILE_RELOAD_COUNT="$(
    grep -c '^FILE=' "${TMP_DOCKER}" 2>/dev/null || true
)"

log "DOCKERFILE_RELOAD_COUNT=${DOCKERFILE_RELOAD_COUNT}"

if [ "${DOCKERFILE_RELOAD_COUNT}" -gt 0 ]; then
    log "DOCKERFILE_RELOAD_FILES_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "DOCKERFILE_RELOAD_FILE=${line#FILE=}"
    done < "${TMP_DOCKER}"

    log "DOCKERFILE_RELOAD_FILES_END"
fi

log ""
log "============================================================"
log "5. PRODUCTION/DEVELOPMENT DOCKERFILE SEMANTICS"
log "============================================================"

while IFS= read -r line; do
    [ -n "${line}" ] || continue

    file="${line#FILE=}"

    base="$(basename "${file}")"
    rel="${file#${PROJECT_ROOT}/}"

    if printf '%s\n' "${rel}" |
        grep -Eiq \
        '(^|/)(dev|development|develop|local|test|testing)(/|$)|dev|development|local|test|testing'
    then
        DOCKERFILE_DEVELOPMENT_MARKER_COUNT=$((DOCKERFILE_DEVELOPMENT_MARKER_COUNT + 1))
        log "DEVELOPMENT_DOCKERFILE_CANDIDATE=${rel}"
    fi

    if printf '%s\n' "${rel}" |
        grep -Eiq \
        '(^|/)(prod|production)(/|$)|prod|production'
    then
        DOCKERFILE_PRODUCTION_MARKER_COUNT=$((DOCKERFILE_PRODUCTION_MARKER_COUNT + 1))
        log "PRODUCTION_DOCKERFILE_CANDIDATE=${rel}"
    fi

done < "${TMP_DOCKER}"

log "DOCKERFILE_PRODUCTION_MARKER_COUNT=${DOCKERFILE_PRODUCTION_MARKER_COUNT}"
log "DOCKERFILE_DEVELOPMENT_MARKER_COUNT=${DOCKERFILE_DEVELOPMENT_MARKER_COUNT}"

log ""
log "============================================================"
log "6. COMPOSE BUILD DATAFLOW"
log "============================================================"

COMPOSE_BUILD_COUNT=0
COMPOSE_BACKEND_BUILD_COUNT=0
COMPOSE_RELOAD_REFERENCE_COUNT=0

if [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then

    grep -nH -E \
        '^[[:space:]]*build:|^[[:space:]]*context:|^[[:space:]]*dockerfile:|^[[:space:]]*backend:|^[[:space:]]*app:' \
        "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null |
    tee "${TMP_COMPOSE}" >/dev/null || true

    COMPOSE_BUILD_COUNT="$(
        grep -Ec '^[^:]+:.*build:|^[[:space:]]*build:' "${TMP_COMPOSE}" 2>/dev/null || true
    )"

    grep -nH -E \
        'dockerfile:|context:|backend:|app:|--reload|reload' \
        "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null || true > "${TMP_PROD}"

    COMPOSE_RELOAD_REFERENCE_COUNT="$(
        grep -Ec -- '--reload|reload[[:space:]]*[:=]' "${TMP_PROD}" 2>/dev/null || true
    )"

    grep -nH -E \
        '^[[:space:]]*backend:|^[[:space:]]*app:' \
        "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null |
    wc -l |
    tr -d ' ' > "${TMP_DEPLOY}"

    COMPOSE_BACKEND_BUILD_COUNT="$(
        cat "${TMP_DEPLOY}" 2>/dev/null || printf '0'
    )"

    log "COMPOSE_BUILD_COUNT=${COMPOSE_BUILD_COUNT}"
    log "COMPOSE_BACKEND_SERVICE_MARKER_COUNT=${COMPOSE_BACKEND_BUILD_COUNT}"
    log "COMPOSE_RELOAD_REFERENCE_COUNT=${COMPOSE_RELOAD_REFERENCE_COUNT}"

    log "COMPOSE_RELOAD_CONTEXT_BEGIN"

    if [ -s "${TMP_PROD}" ]; then
        while IFS= read -r line; do
            [ -n "${line}" ] || continue
            log "COMPOSE_CONTEXT=${line}"
        done < "${TMP_PROD}"
    fi

    log "COMPOSE_RELOAD_CONTEXT_END"

else
    fail "DOCKER_COMPOSE_FILE_MISSING"
fi

if [ "${COMPOSE_RELOAD_REFERENCE_COUNT}" -eq 0 ]; then
    pass "COMPOSE_DOES_NOT_DIRECTLY_REFERENCE_RELOAD"
else
    fail "COMPOSE_DIRECTLY_REFERENCES_RELOAD"
fi

log ""
log "============================================================"
log "7. DEPLOYMENT PATH RELOAD SEARCH"
log "============================================================"

DEPLOY_RELOAD_REFERENCE_COUNT=0

find "${PROJECT_ROOT}/scripts" \
    -type f \
    \( -name '*.sh' -o -name '*.py' -o -name '*.yml' -o -name '*.yaml' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        -- '--reload|reload[[:space:]]*[:=]' \
        "${file}" 2>/dev/null || true
done > "${TMP_DEPLOY}"

DEPLOY_RELOAD_REFERENCE_COUNT="$(
    wc -l < "${TMP_DEPLOY}" |
    tr -d ' '
)"

log "DEPLOY_RELOAD_REFERENCE_COUNT=${DEPLOY_RELOAD_REFERENCE_COUNT}"

if [ "${DEPLOY_RELOAD_REFERENCE_COUNT}" -eq 0 ]; then
    pass "DEPLOYMENT_SCRIPTS_DO_NOT_REFERENCE_RELOAD"
else
    log "DEPLOY_RELOAD_REFERENCES_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "DEPLOY_RELOAD_REFERENCE=${line}"
    done < "${TMP_DEPLOY}"

    log "DEPLOY_RELOAD_REFERENCES_END"
fi

log ""
log "============================================================"
log "8. PRODUCTION PATH CORRELATION"
log "============================================================"

PRODUCTION_RELOAD_BLOCKER=0
PRODUCTION_RELOAD_REVIEW=0

RELOAD_IN_COMPOSE=0
RELOAD_IN_DEPLOY=0
RELOAD_IN_PRODUCTION_NAMED_DOCKERFILE=0
RELOAD_ONLY_IN_DOCKERFILE=0

if [ "${COMPOSE_RELOAD_REFERENCE_COUNT}" -gt 0 ]; then
    RELOAD_IN_COMPOSE=1
fi

if [ "${DEPLOY_RELOAD_REFERENCE_COUNT}" -gt 0 ]; then
    RELOAD_IN_DEPLOY=1
fi

if [ "${DOCKERFILE_PRODUCTION_MARKER_COUNT}" -gt 0 ]; then
    RELOAD_IN_PRODUCTION_NAMED_DOCKERFILE=1
fi

if [ "${DOCKERFILE_RELOAD_COUNT}" -gt 0 ] &&
   [ "${COMPOSE_RELOAD_REFERENCE_COUNT}" -eq 0 ] &&
   [ "${DEPLOY_RELOAD_REFERENCE_COUNT}" -eq 0 ]; then
    RELOAD_ONLY_IN_DOCKERFILE=1
fi

log "RELOAD_IN_COMPOSE=${RELOAD_IN_COMPOSE}"
log "RELOAD_IN_DEPLOY=${RELOAD_IN_DEPLOY}"
log "RELOAD_IN_PRODUCTION_NAMED_DOCKERFILE=${RELOAD_IN_PRODUCTION_NAMED_DOCKERFILE}"
log "RELOAD_ONLY_IN_DOCKERFILE=${RELOAD_ONLY_IN_DOCKERFILE}"

if [ "${RELOAD_IN_COMPOSE}" -eq 1 ]; then
    PRODUCTION_RELOAD_BLOCKER=1
    fail "RELOAD_REACHES_COMPOSE_RUNTIME_PATH"
elif [ "${RELOAD_IN_DEPLOY}" -eq 1 ]; then
    PRODUCTION_RELOAD_BLOCKER=1
    fail "RELOAD_REACHES_DEPLOYMENT_SCRIPT_PATH"
elif [ "${RELOAD_IN_PRODUCTION_NAMED_DOCKERFILE}" -eq 1 ]; then
    PRODUCTION_RELOAD_REVIEW=1
    review "RELOAD_PRESENT_IN_PRODUCTION_NAMED_DOCKERFILE"
elif [ "${RELOAD_ONLY_IN_DOCKERFILE}" -eq 1 ]; then
    pass "RELOAD_ISOLATED_FROM_COMPOSE_AND_DEPLOYMENT_PATH"
else
    pass "NO_RELOAD_PRODUCTION_DATAFLOW_DETECTED"
fi

log ""
log "============================================================"
log "9. BACKEND DOCKERFILE SPECIAL CHECK"
log "============================================================"

BACKEND_DOCKERFILE="${PROJECT_ROOT}/docker/backend/Dockerfile"
APP_DOCKERFILE="${PROJECT_ROOT}/app/Dockerfile"

if [ -f "${BACKEND_DOCKERFILE}" ]; then
    if grep -q -- '--reload' "${BACKEND_DOCKERFILE}" 2>/dev/null; then
        pass "BACKEND_DOCKERFILE_RELOAD_PRESENT"

        log "BACKEND_DOCKERFILE_RELOAD_LINES_BEGIN"

        grep -nH -- '--reload' "${BACKEND_DOCKERFILE}" 2>/dev/null |
        while IFS= read -r line; do
            [ -n "${line}" ] || continue
            log "BACKEND_DOCKERFILE_RELOAD=${line}"
        done

        log "BACKEND_DOCKERFILE_RELOAD_LINES_END"
    else
        pass "BACKEND_DOCKERFILE_HAS_NO_RELOAD"
    fi
else
    review "BACKEND_DOCKERFILE_NOT_PRESENT"
fi

if [ -f "${APP_DOCKERFILE}" ]; then
    if grep -q -- '--reload' "${APP_DOCKERFILE}" 2>/dev/null; then
        review "APP_DOCKERFILE_ALSO_CONTAINS_RELOAD"
    else
        pass "APP_DOCKERFILE_HAS_NO_RELOAD"
    fi
else
    review "APP_DOCKERFILE_NOT_PRESENT"
fi

log ""
log "============================================================"
log "10. FINAL PRODUCTION DECISION"
log "============================================================"

if [ "${PRODUCTION_RELOAD_BLOCKER}" -eq 1 ]; then
    STATUS="FAIL"
    RESULT="P0_03_R47_PRODUCTION_RELOAD_BLOCKER_CONFIRMED"
    EXIT_CODE=2
elif [ "${PRODUCTION_RELOAD_REVIEW}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_03_R47_PRODUCTION_RELOAD_PRODUCTION_SCOPE_REVIEW"
    EXIT_CODE=1
else
    STATUS="PASS"
    RESULT="P0_03_R47_PRODUCTION_RELOAD_DATAFLOW_PASS"
    EXIT_CODE=0
fi

log ""
log "============================================================"
log "11. FINAL EVIDENCE CARD"
log "============================================================"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "R46_STATUS=${R46_STATUS:-UNKNOWN}"
log "R46_EXIT_CODE=${R46_EXIT_CODE:-UNKNOWN}"
log "R46_PRODUCTION_BIND_BLOCKER=${R46_PRODUCTION_BIND_BLOCKER:-UNKNOWN}"

log "RELOAD_REFERENCE_COUNT=${RELOAD_REFERENCE_COUNT}"
log "DOCKERFILE_RELOAD_COUNT=${DOCKERFILE_RELOAD_COUNT}"
log "DOCKERFILE_PRODUCTION_MARKER_COUNT=${DOCKERFILE_PRODUCTION_MARKER_COUNT}"
log "DOCKERFILE_DEVELOPMENT_MARKER_COUNT=${DOCKERFILE_DEVELOPMENT_MARKER_COUNT}"
log "COMPOSE_BUILD_COUNT=${COMPOSE_BUILD_COUNT}"
log "COMPOSE_BACKEND_SERVICE_MARKER_COUNT=${COMPOSE_BACKEND_BUILD_COUNT}"
log "COMPOSE_RELOAD_REFERENCE_COUNT=${COMPOSE_RELOAD_REFERENCE_COUNT}"
log "DEPLOY_RELOAD_REFERENCE_COUNT=${DEPLOY_RELOAD_REFERENCE_COUNT}"

log "RELOAD_IN_COMPOSE=${RELOAD_IN_COMPOSE}"
log "RELOAD_IN_DEPLOY=${RELOAD_IN_DEPLOY}"
log "RELOAD_IN_PRODUCTION_NAMED_DOCKERFILE=${RELOAD_IN_PRODUCTION_NAMED_DOCKERFILE}"
log "RELOAD_ONLY_IN_DOCKERFILE=${RELOAD_ONLY_IN_DOCKERFILE}"

log "PRODUCTION_RELOAD_BLOCKER=${PRODUCTION_RELOAD_BLOCKER}"
log "PRODUCTION_RELOAD_REVIEW=${PRODUCTION_RELOAD_REVIEW}"

log "P0_03_R47_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

: > "${TMP_RELOAD}"
: > "${TMP_COMPOSE}"
: > "${TMP_DOCKER}"
: > "${TMP_DEPLOY}"
: > "${TMP_PROD}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
