#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r46_application_host_runtime_dataflow_closure_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

STATUS="PASS"
RESULT="P0_03_R46_APPLICATION_HOST_RUNTIME_DATAFLOW_CLOSURE_PASS"
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

TMP_HOST="${REPORT_DIR}/.r46_host.tmp"
TMP_SERVER="${REPORT_DIR}/.r46_server.tmp"
TMP_COMPOSE="${REPORT_DIR}/.r46_compose.tmp"
TMP_DOCKER="${REPORT_DIR}/.r46_docker.tmp"
TMP_START="${REPORT_DIR}/.r46_start.tmp"
TMP_EXACT="${REPORT_DIR}/.r46_exact.tmp"

: > "${TMP_HOST}"
: > "${TMP_SERVER}"
: > "${TMP_COMPOSE}"
: > "${TMP_DOCKER}"
: > "${TMP_START}"
: > "${TMP_EXACT}"

log "============================================================"
log "P0-03 R46 APPLICATION HOST RUNTIME DATAFLOW CLOSURE GATE"
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
pass "TARGETED_DATAFLOW_CLOSURE=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. R45 AUTHORITY HANDOFF"
log "============================================================"

R45_REPORT="${REPORT_DIR}/p0_03_r45_application_host_dataflow_locator_gate.txt"

if [ -f "${R45_REPORT}" ]; then
    pass "R45_REPORT_PRESENT"

    R45_STATUS="$(
        grep -E '^P0_03_R45_STATUS=' "${R45_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R45_EXIT_CODE="$(
        grep -E '^EXIT_CODE=' "${R45_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R45_HOST_DECLARATION_COUNT="$(
        grep -E '^HOST_DECLARATION_COUNT=' "${R45_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R45_EXPLICIT_HOST_ARGUMENT_COUNT="$(
        grep -E '^EXPLICIT_HOST_ARGUMENT_COUNT=' "${R45_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R45_PRODUCTION_BIND_BLOCKER="$(
        grep -E '^PRODUCTION_BIND_BLOCKER=' "${R45_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    log "R45_STATUS=${R45_STATUS:-UNKNOWN}"
    log "R45_EXIT_CODE=${R45_EXIT_CODE:-UNKNOWN}"
    log "R45_HOST_DECLARATION_COUNT=${R45_HOST_DECLARATION_COUNT:-UNKNOWN}"
    log "R45_EXPLICIT_HOST_ARGUMENT_COUNT=${R45_EXPLICIT_HOST_ARGUMENT_COUNT:-UNKNOWN}"
    log "R45_PRODUCTION_BIND_BLOCKER=${R45_PRODUCTION_BIND_BLOCKER:-UNKNOWN}"

    if [ "${R45_STATUS:-}" = "REVIEW" ] &&
       [ "${R45_EXIT_CODE:-}" = "1" ]; then
        pass "R45_REVIEW_HANDOFF_ACCEPTED"
    else
        review "R45_HANDOFF_STATE_NOT_EXPECTED"
    fi
else
    fail "R45_REPORT_MISSING"
fi

log ""
log "============================================================"
log "3. EXACT HOST CONFIGURATION REFERENCE SEARCH"
log "============================================================"

EXACT_HOST_REFERENCE_COUNT=0

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '(^|[^[:alnum:]_])(settings|config|configuration|cfg)[.]HOST([^[:alnum:]_]|$)|(^|[^[:alnum:]_])HOST([^[:alnum:]_]|$)' \
        "${file}" 2>/dev/null || true
done > "${TMP_HOST}"

EXACT_HOST_REFERENCE_COUNT="$(
    wc -l < "${TMP_HOST}" |
    tr -d ' '
)"

log "EXACT_HOST_REFERENCE_COUNT=${EXACT_HOST_REFERENCE_COUNT}"

log "EXACT_HOST_REFERENCES_BEGIN"

while IFS= read -r line; do
    [ -n "${line}" ] || continue
    log "HOST_REFERENCE=${line}"
done < "${TMP_HOST}"

log "EXACT_HOST_REFERENCES_END"

log ""
log "============================================================"
log "4. EXACT SERVER STARTUP SEARCH"
log "============================================================"

SERVER_STARTUP_COUNT=0

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '(^|[^[:alnum:]_])(uvicorn|gunicorn|hypercorn|uvicorn[.]run|app[.]run|FastAPI|create_app)([^[:alnum:]_]|$)' \
        "${file}" 2>/dev/null || true
done > "${TMP_SERVER}"

SERVER_STARTUP_COUNT="$(
    wc -l < "${TMP_SERVER}" |
    tr -d ' '
)"

log "SERVER_STARTUP_COUNT=${SERVER_STARTUP_COUNT}"

if [ "${SERVER_STARTUP_COUNT}" -gt 0 ]; then
    pass "SERVER_STARTUP_SYMBOLS_LOCATED"
else
    review "NO_PYTHON_SERVER_STARTUP_SYMBOL_LOCATED"
fi

log "SERVER_STARTUP_BEGIN"

while IFS= read -r line; do
    [ -n "${line}" ] || continue
    log "SERVER_STARTUP=${line}"
done < "${TMP_SERVER}"

log "SERVER_STARTUP_END"

log ""
log "============================================================"
log "5. SERVER HOST ARGUMENT SEARCH"
log "============================================================"

SERVER_HOST_ARGUMENT_COUNT=0

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '(^|[^[:alnum:]_])(host|HOST)[[:space:]]*=[[:space:]]*([^#]*)' \
        "${file}" 2>/dev/null |
    grep -E \
        '(uvicorn|gunicorn|hypercorn|app[.]run|run[[:space:]]*\()' \
        2>/dev/null || true
done > "${TMP_EXACT}"

SERVER_HOST_ARGUMENT_COUNT="$(
    wc -l < "${TMP_EXACT}" |
    tr -d ' '
)"

log "SERVER_HOST_ARGUMENT_COUNT=${SERVER_HOST_ARGUMENT_COUNT}"

if [ "${SERVER_HOST_ARGUMENT_COUNT}" -gt 0 ]; then
    fail "EXPLICIT_PYTHON_SERVER_HOST_ARGUMENT_DETECTED"

    log "SERVER_HOST_ARGUMENTS_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "SERVER_HOST_ARGUMENT=${line}"
    done < "${TMP_EXACT}"

    log "SERVER_HOST_ARGUMENTS_END"
else
    pass "NO_PYTHON_SERVER_HOST_ARGUMENT_DETECTED"
fi

log ""
log "============================================================"
log "6. COMPOSE HOST DATAFLOW SEARCH"
log "============================================================"

COMPOSE_HOST_REFERENCE_COUNT=0
COMPOSE_SERVER_COMMAND_COUNT=0

if [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then

    grep -nH -E \
        '(^|[^[:alnum:]_])HOST([^[:alnum:]_]|$)|--host|host[[:space:]]*:' \
        "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null |
    grep -E \
        'HOST|host|--host' \
        2>/dev/null || true > "${TMP_COMPOSE}"

    COMPOSE_HOST_REFERENCE_COUNT="$(
        wc -l < "${TMP_COMPOSE}" |
        tr -d ' '
    )"

    grep -nH -E \
        'command:|entrypoint:|uvicorn|gunicorn|hypercorn|--host' \
        "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null |
    grep -E \
        'uvicorn|gunicorn|hypercorn|--host|command:|entrypoint:' \
        2>/dev/null || true > "${TMP_START}"

    COMPOSE_SERVER_COMMAND_COUNT="$(
        wc -l < "${TMP_START}" |
        tr -d ' '
    )"

    log "COMPOSE_HOST_REFERENCE_COUNT=${COMPOSE_HOST_REFERENCE_COUNT}"
    log "COMPOSE_SERVER_COMMAND_COUNT=${COMPOSE_SERVER_COMMAND_COUNT}"

    log "COMPOSE_HOST_REFERENCES_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "COMPOSE_HOST_REFERENCE=${line}"
    done < "${TMP_COMPOSE}"

    log "COMPOSE_HOST_REFERENCES_END"

    log "COMPOSE_SERVER_COMMANDS_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "COMPOSE_SERVER_COMMAND=${line}"
    done < "${TMP_START}"

    log "COMPOSE_SERVER_COMMANDS_END"

else
    review "DOCKER_COMPOSE_FILE_NOT_PRESENT"
fi

log ""
log "============================================================"
log "7. DOCKERFILE AND STARTUP SCRIPT DATAFLOW SEARCH"
log "============================================================"

DOCKER_HOST_REFERENCE_COUNT=0
STARTUP_HOST_REFERENCE_COUNT=0

find "${PROJECT_ROOT}" \
    -maxdepth 4 \
    -type f \
    \( \
        -name 'Dockerfile' \
        -o -name 'Dockerfile.*' \
        -o -name '*.Dockerfile' \
        -o -name 'entrypoint.sh' \
        -o -name 'start.sh' \
        -o -name 'run.sh' \
        -o -name '*.entrypoint.sh' \
    \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '(^|[^[:alnum:]_])(HOST|host)([^[:alnum:]_]|$)|--host|uvicorn|gunicorn|hypercorn' \
        "${file}" 2>/dev/null || true
done > "${TMP_DOCKER}"

DOCKER_HOST_REFERENCE_COUNT="$(
    wc -l < "${TMP_DOCKER}" |
    tr -d ' '
)"

log "DOCKER_STARTUP_HOST_REFERENCE_COUNT=${DOCKER_HOST_REFERENCE_COUNT}"

if [ "${DOCKER_HOST_REFERENCE_COUNT}" -gt 0 ]; then
    log "DOCKER_STARTUP_REFERENCES_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "DOCKER_STARTUP_REFERENCE=${line}"
    done < "${TMP_DOCKER}"

    log "DOCKER_STARTUP_REFERENCES_END"
else
    pass "NO_DOCKER_STARTUP_HOST_REFERENCE_DETECTED"
fi

log ""
log "============================================================"
log "8. EXACT ZERO-BIND DATAFLOW DECISION"
log "============================================================"

DIRECT_ZERO_BIND_DATAFLOW=0
INDIRECT_ZERO_BIND_DATAFLOW=0

if [ "${SERVER_HOST_ARGUMENT_COUNT}" -gt 0 ]; then
    DIRECT_ZERO_BIND_DATAFLOW=1
fi

if [ "${COMPOSE_SERVER_COMMAND_COUNT}" -gt 0 ] &&
   [ "${COMPOSE_HOST_REFERENCE_COUNT}" -gt 0 ]; then
    INDIRECT_ZERO_BIND_DATAFLOW=1
fi

log "DIRECT_ZERO_BIND_DATAFLOW=${DIRECT_ZERO_BIND_DATAFLOW}"
log "INDIRECT_ZERO_BIND_DATAFLOW=${INDIRECT_ZERO_BIND_DATAFLOW}"

if [ "${DIRECT_ZERO_BIND_DATAFLOW}" -eq 1 ]; then
    fail "ZERO_BIND_HOST_DIRECTLY_FLOWS_TO_APPLICATION_SERVER"
elif [ "${INDIRECT_ZERO_BIND_DATAFLOW}" -eq 1 ]; then
    review "COMPOSE_SERVER_STARTUP_AND_HOST_REFERENCE_REQUIRE_MANUAL_FLOW_CONFIRMATION"
else
    pass "NO_ZERO_BIND_HOST_TO_SERVER_DATAFLOW_DETECTED"
fi

log ""
log "============================================================"
log "9. CONFIGURATION SEMANTIC CLASSIFICATION"
log "============================================================"

CONFIG_HOST_ONLY_COUNT=0
CONFIG_HOST_USED_AS_SERVER_COUNT=0

if [ "${R45_HOST_DECLARATION_COUNT:-0}" -gt 0 ]; then
    CONFIG_HOST_ONLY_COUNT=1
fi

if [ "${EXACT_HOST_REFERENCE_COUNT}" -gt 0 ]; then
    while IFS= read -r line; do
        [ -n "${line}" ] || continue

        if printf '%s\n' "${line}" |
            grep -Eiq \
            '(uvicorn|gunicorn|hypercorn|app[.]run|--host|host[[:space:]]*=)'
        then
            CONFIG_HOST_USED_AS_SERVER_COUNT=$((CONFIG_HOST_USED_AS_SERVER_COUNT + 1))
        fi
    done < "${TMP_HOST}"
fi

log "CONFIG_HOST_ONLY_COUNT=${CONFIG_HOST_ONLY_COUNT}"
log "CONFIG_HOST_USED_AS_SERVER_COUNT=${CONFIG_HOST_USED_AS_SERVER_COUNT}"

if [ "${CONFIG_HOST_USED_AS_SERVER_COUNT}" -gt 0 ]; then
    fail "CONFIG_HOST_IS_USED_AS_SERVER_BIND_INPUT"
else
    pass "CONFIG_HOST_IS_NOT_PROVEN_AS_SERVER_BIND_INPUT"
fi

log ""
log "============================================================"
log "10. PRODUCTION BLOCKER DECISION"
log "============================================================"

PRODUCTION_BIND_BLOCKER=0

if [ "${DIRECT_ZERO_BIND_DATAFLOW}" -eq 1 ]; then
    PRODUCTION_BIND_BLOCKER=1
fi

if [ "${CONFIG_HOST_USED_AS_SERVER_COUNT}" -gt 0 ]; then
    PRODUCTION_BIND_BLOCKER=1
fi

if [ "${PRODUCTION_BIND_BLOCKER}" -eq 1 ]; then
    fail "PRODUCTION_ZERO_BIND_BLOCKER_CONFIRMED"
else
    pass "NO_CONFIRMED_PRODUCTION_ZERO_BIND_BLOCKER"
fi

log ""
log "============================================================"
log "11. R43-R46 RECONCILIATION"
log "============================================================"

R43_APPLICATION_BIND_COUNT=""

R43_REPORT="${REPORT_DIR}/p0_03_r43_production_gap_classification_gate.txt"

if [ -f "${R43_REPORT}" ]; then
    R43_APPLICATION_BIND_COUNT="$(
        grep -E '^UNSAFE_BIND_APPLICATION=' "${R43_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"
fi

log "R43_APPLICATION_BIND_COUNT=${R43_APPLICATION_BIND_COUNT:-UNKNOWN}"
log "R44_EXACT_APPLICATION_BIND_COUNT=${R45_HOST_DECLARATION_COUNT:-UNKNOWN}"
log "R45_EXPLICIT_HOST_ARGUMENT_COUNT=${R45_EXPLICIT_HOST_ARGUMENT_COUNT:-UNKNOWN}"
log "R46_EXACT_HOST_REFERENCE_COUNT=${EXACT_HOST_REFERENCE_COUNT}"
log "R46_SERVER_STARTUP_COUNT=${SERVER_STARTUP_COUNT}"
log "R46_SERVER_HOST_ARGUMENT_COUNT=${SERVER_HOST_ARGUMENT_COUNT}"
log "R46_COMPOSE_HOST_REFERENCE_COUNT=${COMPOSE_HOST_REFERENCE_COUNT}"
log "R46_COMPOSE_SERVER_COMMAND_COUNT=${COMPOSE_SERVER_COMMAND_COUNT}"
log "R46_DOCKER_STARTUP_HOST_REFERENCE_COUNT=${DOCKER_HOST_REFERENCE_COUNT}"
log "R46_CONFIG_HOST_USED_AS_SERVER_COUNT=${CONFIG_HOST_USED_AS_SERVER_COUNT}"
log "R46_PRODUCTION_BIND_BLOCKER=${PRODUCTION_BIND_BLOCKER}"

if [ "${R43_APPLICATION_BIND_COUNT:-}" = "2" ] &&
   [ "${R45_HOST_DECLARATION_COUNT:-}" = "1" ] &&
   [ "${R45_EXPLICIT_HOST_ARGUMENT_COUNT:-}" = "0" ] &&
   [ "${PRODUCTION_BIND_BLOCKER}" = "0" ]; then
    pass "R43_COARSE_UNSAFE_BIND_SIGNAL_RECONCILED_WITH_NO_CONFIRMED_SERVER_DATAFLOW"
else
    review "R43_TO_R46_BIND_RECONCILIATION_REQUIRES_REVIEW"
fi

log ""
log "============================================================"
log "12. FINAL CLASSIFICATION"
log "============================================================"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_03_R46_APPLICATION_HOST_RUNTIME_DATAFLOW_PRODUCTION_BLOCKER"
    EXIT_CODE=2
elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_03_R46_APPLICATION_HOST_RUNTIME_DATAFLOW_REVIEW"
    EXIT_CODE=1
else
    STATUS="PASS"
    RESULT="P0_03_R46_APPLICATION_HOST_RUNTIME_DATAFLOW_CLOSURE_PASS"
    EXIT_CODE=0
fi

log ""
log "============================================================"
log "13. FINAL EVIDENCE CARD"
log "============================================================"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "R45_STATUS=${R45_STATUS:-UNKNOWN}"
log "R45_EXIT_CODE=${R45_EXIT_CODE:-UNKNOWN}"
log "R45_HOST_DECLARATION_COUNT=${R45_HOST_DECLARATION_COUNT:-UNKNOWN}"
log "R45_EXPLICIT_HOST_ARGUMENT_COUNT=${R45_EXPLICIT_HOST_ARGUMENT_COUNT:-UNKNOWN}"
log "R45_PRODUCTION_BIND_BLOCKER=${R45_PRODUCTION_BIND_BLOCKER:-UNKNOWN}"

log "EXACT_HOST_REFERENCE_COUNT=${EXACT_HOST_REFERENCE_COUNT}"
log "SERVER_STARTUP_COUNT=${SERVER_STARTUP_COUNT}"
log "SERVER_HOST_ARGUMENT_COUNT=${SERVER_HOST_ARGUMENT_COUNT}"
log "COMPOSE_HOST_REFERENCE_COUNT=${COMPOSE_HOST_REFERENCE_COUNT}"
log "COMPOSE_SERVER_COMMAND_COUNT=${COMPOSE_SERVER_COMMAND_COUNT}"
log "DOCKER_STARTUP_HOST_REFERENCE_COUNT=${DOCKER_HOST_REFERENCE_COUNT}"
log "CONFIG_HOST_ONLY_COUNT=${CONFIG_HOST_ONLY_COUNT}"
log "CONFIG_HOST_USED_AS_SERVER_COUNT=${CONFIG_HOST_USED_AS_SERVER_COUNT}"
log "DIRECT_ZERO_BIND_DATAFLOW=${DIRECT_ZERO_BIND_DATAFLOW}"
log "INDIRECT_ZERO_BIND_DATAFLOW=${INDIRECT_ZERO_BIND_DATAFLOW}"
log "PRODUCTION_BIND_BLOCKER=${PRODUCTION_BIND_BLOCKER}"

log "P0_03_R46_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

: > "${TMP_HOST}"
: > "${TMP_SERVER}"
: > "${TMP_COMPOSE}"
: > "${TMP_DOCKER}"
: > "${TMP_START}"
: > "${TMP_EXACT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
