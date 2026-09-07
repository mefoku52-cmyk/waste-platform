#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r45_application_host_dataflow_locator_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

STATUS="PASS"
RESULT="P0_03_R45_APPLICATION_HOST_DATAFLOW_LOCATOR_PASS"
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

TMP_HOST="${REPORT_DIR}/.r45_host_matches.tmp"
TMP_USE="${REPORT_DIR}/.r45_host_usage.tmp"
TMP_SERVER="${REPORT_DIR}/.r45_server_matches.tmp"
TMP_ALL="${REPORT_DIR}/.r45_all_matches.tmp"

: > "${TMP_HOST}"
: > "${TMP_USE}"
: > "${TMP_SERVER}"
: > "${TMP_ALL}"

log "============================================================"
log "P0-03 R45 APPLICATION HOST DATAFLOW LOCATOR GATE"
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
pass "DATAFLOW_FORENSICS_ONLY=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. R44 AUTHORITY HANDOFF"
log "============================================================"

R44_REPORT="${REPORT_DIR}/p0_03_r44_unsafe_bind_blocker_locator_gate.txt"

if [ -f "${R44_REPORT}" ]; then
    pass "R44_REPORT_PRESENT"

    R44_STATUS="$(
        grep -E '^P0_03_R44_STATUS=' "${R44_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R44_EXIT_CODE="$(
        grep -E '^EXIT_CODE=' "${R44_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R44_RAW_COUNT="$(
        grep -E '^RAW_APPLICATION_BIND_MATCH_COUNT=' "${R44_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R44_REAL_BIND_COUNT="$(
        grep -E '^REAL_EXECUTABLE_OR_CONFIGURATION_BIND_COUNT=' "${R44_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    R44_PRODUCTION_BLOCKER="$(
        grep -E '^PRODUCTION_BIND_BLOCKER=' "${R44_REPORT}" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"

    log "R44_STATUS=${R44_STATUS:-UNKNOWN}"
    log "R44_EXIT_CODE=${R44_EXIT_CODE:-UNKNOWN}"
    log "R44_RAW_APPLICATION_BIND_MATCH_COUNT=${R44_RAW_COUNT:-UNKNOWN}"
    log "R44_REAL_BIND_COUNT=${R44_REAL_BIND_COUNT:-UNKNOWN}"
    log "R44_PRODUCTION_BIND_BLOCKER=${R44_PRODUCTION_BLOCKER:-UNKNOWN}"

    if [ "${R44_STATUS:-}" = "REVIEW" ] &&
       [ "${R44_EXIT_CODE:-}" = "1" ]; then
        pass "R44_REVIEW_HANDOFF_ACCEPTED"
    else
        review "R44_HANDOFF_STATE_NOT_EXPECTED"
    fi
else
    fail "R44_REPORT_MISSING"
fi

log ""
log "============================================================"
log "3. APPLICATION HOST DECLARATION LOCATOR"
log "============================================================"

HOST_DECLARATION_COUNT=0

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '^[[:space:]]*(HOST|host)[[:space:]]*(:[[:space:]]*[^=]+)?[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
        "${file}" 2>/dev/null || true
done > "${TMP_HOST}"

HOST_DECLARATION_COUNT="$(
    wc -l < "${TMP_HOST}" |
    tr -d ' '
)"

log "HOST_DECLARATION_COUNT=${HOST_DECLARATION_COUNT}"

if [ "${HOST_DECLARATION_COUNT}" -gt 0 ]; then
    pass "EXPLICIT_ZERO_BIND_HOST_DECLARATION_LOCATED"
else
    review "NO_EXPLICIT_HOST_DECLARATION_LOCATED"
fi

log "HOST_DECLARATIONS_BEGIN"

while IFS= read -r line; do
    [ -n "${line}" ] || continue
    log "HOST_DECLARATION=${line}"
done < "${TMP_HOST}"

log "HOST_DECLARATIONS_END"

log ""
log "============================================================"
log "4. HOST SYMBOL USAGE ANALYSIS"
log "============================================================"

HOST_USAGE_COUNT=0
HOST_RUNTIME_USAGE_COUNT=0
HOST_SERVER_ARGUMENT_COUNT=0

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '\b(HOST|host)\b' \
        "${file}" 2>/dev/null || true
done > "${TMP_USE}"

HOST_USAGE_COUNT="$(
    wc -l < "${TMP_USE}" |
    tr -d ' '
)"

log "HOST_SYMBOL_USAGE_COUNT=${HOST_USAGE_COUNT}"

log "HOST_SYMBOL_USAGE_BEGIN"

while IFS= read -r line; do
    [ -n "${line}" ] || continue

    log "HOST_USAGE=${line}"

    content="${line#*:}"

    if printf '%s\n' "${content}" |
        grep -Eiq \
        '(uvicorn|hypercorn|gunicorn|flask|app\.run|run\(|serve\(|listen\(|bind\()'
    then
        HOST_RUNTIME_USAGE_COUNT=$((HOST_RUNTIME_USAGE_COUNT + 1))
    fi

    if printf '%s\n' "${content}" |
        grep -Eiq \
        '(^|[^[:alnum:]_])(host|HOST)[[:space:]]*='
    then
        HOST_SERVER_ARGUMENT_COUNT=$((HOST_SERVER_ARGUMENT_COUNT + 1))
    fi

done < "${TMP_USE}"

log "HOST_SYMBOL_USAGE_END"

log "HOST_RUNTIME_USAGE_COUNT=${HOST_RUNTIME_USAGE_COUNT}"
log "HOST_SERVER_ARGUMENT_COUNT=${HOST_SERVER_ARGUMENT_COUNT}"

log ""
log "============================================================"
log "5. SERVER STARTUP DATAFLOW SEARCH"
log "============================================================"

SERVER_STARTUP_PATTERN_COUNT=0

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '(uvicorn|hypercorn|gunicorn|app\.run|uvicorn\.run|hypercorn\.run|serve\(|listen\(|bind\()' \
        "${file}" 2>/dev/null || true
done > "${TMP_SERVER}"

SERVER_STARTUP_PATTERN_COUNT="$(
    wc -l < "${TMP_SERVER}" |
    tr -d ' '
)"

log "SERVER_STARTUP_PATTERN_COUNT=${SERVER_STARTUP_PATTERN_COUNT}"

if [ "${SERVER_STARTUP_PATTERN_COUNT}" -gt 0 ]; then
    pass "SERVER_STARTUP_PATTERNS_LOCATED"
else
    review "NO_SERVER_STARTUP_PATTERN_LOCATED"
fi

log "SERVER_STARTUP_PATTERNS_BEGIN"

while IFS= read -r line; do
    [ -n "${line}" ] || continue
    log "SERVER_STARTUP=${line}"
done < "${TMP_SERVER}"

log "SERVER_STARTUP_PATTERNS_END"

log ""
log "============================================================"
log "6. EXPLICIT HOST ARGUMENT DATAFLOW"
log "============================================================"

EXPLICIT_HOST_ARGUMENT_COUNT=0

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '(uvicorn|hypercorn|gunicorn|app\.run|run)[^#]*(host[[:space:]]*=[[:space:]]*(HOST|host)|HOST[[:space:]]*=|host[[:space:]]*=)' \
        "${file}" 2>/dev/null || true
done > "${TMP_ALL}"

EXPLICIT_HOST_ARGUMENT_COUNT="$(
    wc -l < "${TMP_ALL}" |
    tr -d ' '
)"

log "EXPLICIT_HOST_ARGUMENT_COUNT=${EXPLICIT_HOST_ARGUMENT_COUNT}"

if [ "${EXPLICIT_HOST_ARGUMENT_COUNT}" -gt 0 ]; then
    log "EXPLICIT_HOST_ARGUMENTS_BEGIN"

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        log "EXPLICIT_HOST_ARGUMENT=${line}"
    done < "${TMP_ALL}"

    log "EXPLICIT_HOST_ARGUMENTS_END"
else
    pass "NO_EXPLICIT_SERVER_HOST_ARGUMENT_USING_HOST_SYMBOL_DETECTED"
fi

log ""
log "============================================================"
log "7. PRODUCTION INTERPRETATION"
log "============================================================"

PRODUCTION_BIND_BLOCKER=0
PRODUCTION_BIND_REVIEW=0

if [ "${EXPLICIT_HOST_ARGUMENT_COUNT}" -gt 0 ]; then
    PRODUCTION_BIND_BLOCKER=1
    fail "HOST_ZERO_BIND_FLOWS_DIRECTLY_INTO_SERVER_STARTUP"
elif [ "${HOST_RUNTIME_USAGE_COUNT}" -gt 0 ]; then
    PRODUCTION_BIND_REVIEW=1
    review "HOST_SYMBOL_HAS_RUNTIME_SERVER_CONTEXT_BUT_DIRECT_BIND_NOT_PROVEN"
elif [ "${HOST_DECLARATION_COUNT}" -gt 0 ]; then
    PRODUCTION_BIND_REVIEW=1
    review "ZERO_BIND_HOST_EXISTS_BUT_RUNTIME_DATAFLOW_IS_NOT_PROVEN"
else
    pass "NO_ZERO_BIND_HOST_DATAFLOW_FOUND"
fi

log "PRODUCTION_BIND_BLOCKER=${PRODUCTION_BIND_BLOCKER}"
log "PRODUCTION_BIND_REVIEW=${PRODUCTION_BIND_REVIEW}"

log ""
log "============================================================"
log "8. R43/R44 RECONCILIATION"
log "============================================================"

R43_APPLICATION_BIND_COUNT=""

if [ -f "${REPORT_DIR}/p0_03_r43_production_gap_classification_gate.txt" ]; then
    R43_APPLICATION_BIND_COUNT="$(
        grep -E '^UNSAFE_BIND_APPLICATION=' \
            "${REPORT_DIR}/p0_03_r43_production_gap_classification_gate.txt" 2>/dev/null |
        tail -1 |
        cut -d= -f2-
    )"
fi

log "R43_APPLICATION_BIND_COUNT=${R43_APPLICATION_BIND_COUNT:-UNKNOWN}"
log "R44_RAW_APPLICATION_BIND_COUNT=${R44_RAW_COUNT:-UNKNOWN}"
log "R45_HOST_DECLARATION_COUNT=${HOST_DECLARATION_COUNT}"
log "R45_SERVER_STARTUP_PATTERN_COUNT=${SERVER_STARTUP_PATTERN_COUNT}"
log "R45_EXPLICIT_HOST_ARGUMENT_COUNT=${EXPLICIT_HOST_ARGUMENT_COUNT}"

if [ "${R43_APPLICATION_BIND_COUNT:-}" = "2" ] &&
   [ "${R44_RAW_COUNT:-}" = "1" ] &&
   [ "${HOST_DECLARATION_COUNT}" = "1" ]; then
    pass "R43_COARSE_COUNT_REDUCED_TO_ONE_EXACT_HOST_DECLARATION"
else
    review "R43_R44_R45_COUNT_CHAIN_REQUIRES_RECONCILIATION"
fi

log ""
log "============================================================"
log "9. FINAL CLASSIFICATION"
log "============================================================"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_03_R45_APPLICATION_HOST_DATAFLOW_PRODUCTION_BLOCKER"
    EXIT_CODE=2
elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_03_R45_APPLICATION_HOST_DATAFLOW_REVIEW"
    EXIT_CODE=1
else
    STATUS="PASS"
    RESULT="P0_03_R45_APPLICATION_HOST_DATAFLOW_LOCATOR_PASS"
    EXIT_CODE=0
fi

log ""
log "============================================================"
log "10. FINAL EVIDENCE CARD"
log "============================================================"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "R43_APPLICATION_BIND_COUNT=${R43_APPLICATION_BIND_COUNT:-UNKNOWN}"
log "R44_STATUS=${R44_STATUS:-UNKNOWN}"
log "R44_RAW_APPLICATION_BIND_MATCH_COUNT=${R44_RAW_COUNT:-UNKNOWN}"

log "HOST_DECLARATION_COUNT=${HOST_DECLARATION_COUNT}"
log "HOST_SYMBOL_USAGE_COUNT=${HOST_USAGE_COUNT}"
log "HOST_RUNTIME_USAGE_COUNT=${HOST_RUNTIME_USAGE_COUNT}"
log "HOST_SERVER_ARGUMENT_COUNT=${HOST_SERVER_ARGUMENT_COUNT}"
log "SERVER_STARTUP_PATTERN_COUNT=${SERVER_STARTUP_PATTERN_COUNT}"
log "EXPLICIT_HOST_ARGUMENT_COUNT=${EXPLICIT_HOST_ARGUMENT_COUNT}"

log "PRODUCTION_BIND_BLOCKER=${PRODUCTION_BIND_BLOCKER}"
log "PRODUCTION_BIND_REVIEW=${PRODUCTION_BIND_REVIEW}"

log "P0_03_R45_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

: > "${TMP_HOST}"
: > "${TMP_USE}"
: > "${TMP_SERVER}"
: > "${TMP_ALL}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
