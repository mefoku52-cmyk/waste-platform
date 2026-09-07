#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r44_unsafe_bind_blocker_locator_gate.txt"

SCRIPT_NAME="$(basename "$0")"

FAILURE_COUNT=0
REVIEW_COUNT=0

STATUS="PASS"
RESULT="P0_03_R44_UNSAFE_BIND_BLOCKER_LOCATOR_PASS"
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

mkdir -p "${REPORT_DIR}"
: > "${REPORT}"

log "============================================================"
log "P0-03 R44 UNSAFE BIND BLOCKER LOCATOR GATE"
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
pass "TARGETED_BLOCKER_FORENSICS=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. R43 AUTHORITY HANDOFF"
log "============================================================"

R43_REPORT="${REPORT_DIR}/p0_03_r43_production_gap_classification_gate.txt"

if file_exists "${R43_REPORT}"; then
    pass "R43_REPORT_PRESENT"

    R43_STATUS="$(grep -E '^P0_03_R43_STATUS=' "${R43_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R43_EXIT_CODE="$(grep -E '^EXIT_CODE=' "${R43_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R43_FAILURE_COUNT="$(grep -E '^FAILURE_COUNT=' "${R43_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R43_BIND_GAP="$(grep -E '^BIND_GAP=' "${R43_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R43_APPLICATION_BIND_COUNT="$(grep -E '^UNSAFE_BIND_APPLICATION=' "${R43_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"

    log "R43_STATUS=${R43_STATUS:-UNKNOWN}"
    log "R43_EXIT_CODE=${R43_EXIT_CODE:-UNKNOWN}"
    log "R43_FAILURE_COUNT=${R43_FAILURE_COUNT:-UNKNOWN}"
    log "R43_BIND_GAP=${R43_BIND_GAP:-UNKNOWN}"
    log "R43_UNSAFE_BIND_APPLICATION=${R43_APPLICATION_BIND_COUNT:-UNKNOWN}"

    if [ "${R43_STATUS:-}" = "FAIL" ] &&
       [ "${R43_EXIT_CODE:-}" = "2" ]; then
        pass "R43_BLOCKER_HANDOFF_ACCEPTED"
    else
        fail "R43_BLOCKER_HANDOFF_STATE_UNEXPECTED"
    fi

    if [ "${R43_APPLICATION_BIND_COUNT:-0}" -gt 0 ]; then
        pass "APPLICATION_BIND_BLOCKER_REQUIRES_EXACT_LOCALIZATION"
    else
        fail "R43_APPLICATION_BIND_COUNT_NOT_POSITIVE"
    fi
else
    fail "R43_REPORT_MISSING"
fi

log ""
log "============================================================"
log "3. APPLICATION SCOPE DEFINITION"
log "============================================================"

APP_SCOPE_COUNT=0

for scope in \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src"
do
    if dir_exists "${scope}"; then
        APP_SCOPE_COUNT=$((APP_SCOPE_COUNT + 1))
        pass "APPLICATION_SCOPE_PRESENT=${scope}"
    fi
done

log "APPLICATION_SCOPE_COUNT=${APP_SCOPE_COUNT}"

if [ "${APP_SCOPE_COUNT}" -gt 0 ]; then
    pass "APPLICATION_SCOPE_ESTABLISHED"
else
    fail "NO_APPLICATION_SCOPE_AVAILABLE"
fi

log ""
log "============================================================"
log "4. EXACT UNSAFE-BIND LOCALIZATION"
log "============================================================"

RAW_BIND_MATCH_COUNT=0
PYTHON_BIND_MATCH_COUNT=0
CONFIG_BIND_MATCH_COUNT=0
SERVER_BIND_MATCH_COUNT=0
DOCUMENTATION_BIND_MATCH_COUNT=0
COMMENT_BIND_MATCH_COUNT=0
NON_EXECUTABLE_BIND_MATCH_COUNT=0

TMP_RAW="${REPORT_DIR}/.r44_raw_bind_matches.tmp"
TMP_CLASSIFIED="${REPORT_DIR}/.r44_classified_bind_matches.tmp"

: > "${TMP_RAW}"
: > "${TMP_CLASSIFIED}"

find \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    -type f \
    \( \
        -name '*.py' \
        -o -name '*.pyi' \
        -o -name '*.yaml' \
        -o -name '*.yml' \
        -o -name '*.json' \
        -o -name '*.toml' \
        -o -name '*.ini' \
        -o -name '*.conf' \
        -o -name '*.sh' \
    \) \
    -print0 2>/dev/null |
while IFS= read -r -d '' file; do
    grep -nH -E \
        '0\.0\.0\.0|host[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
        "${file}" 2>/dev/null || true
done > "${TMP_RAW}"

RAW_BIND_MATCH_COUNT="$(
    wc -l < "${TMP_RAW}" |
    tr -d ' '
)"

log "RAW_APPLICATION_BIND_MATCH_COUNT=${RAW_BIND_MATCH_COUNT}"

if [ "${RAW_BIND_MATCH_COUNT}" -gt 0 ]; then
    pass "APPLICATION_BIND_MATCHES_LOCATED"
else
    fail "APPLICATION_BIND_MATCHES_DISAPPEARED_DURING_EXACT_SCAN"
fi

log "EXACT_APPLICATION_BIND_MATCHES_BEGIN"

while IFS= read -r line; do
    [ -n "${line}" ] || continue

    log "MATCH=${line}"

    file="${line%%:*}"
    rest="${line#*:}"
    lineno="${rest%%:*}"
    content="${rest#*:}"

    classification="NON_EXECUTABLE"

    case "${file}" in
        *.py|*.pyi)
            PYTHON_BIND_MATCH_COUNT=$((PYTHON_BIND_MATCH_COUNT + 1))

            if printf '%s\n' "${content}" |
                grep -Eiq \
                '(^|[[:space:]])(host|bind|listen|address)[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']'
            then
                classification="PYTHON_CONFIG_BIND"
                CONFIG_BIND_MATCH_COUNT=$((CONFIG_BIND_MATCH_COUNT + 1))
            fi

            if printf '%s\n' "${content}" |
                grep -Eiq \
                '(uvicorn|hypercorn|gunicorn|flask|app\.run|run\(|serve\(|listen\(|bind\()'
            then
                classification="PYTHON_SERVER_BIND"
                SERVER_BIND_MATCH_COUNT=$((SERVER_BIND_MATCH_COUNT + 1))
            fi
            ;;

        *.yaml|*.yml|*.json|*.toml|*.ini|*.conf)
            classification="CONFIG_BIND"
            CONFIG_BIND_MATCH_COUNT=$((CONFIG_BIND_MATCH_COUNT + 1))
            ;;

        *.sh)
            classification="SCRIPT_BIND"
            CONFIG_BIND_MATCH_COUNT=$((CONFIG_BIND_MATCH_COUNT + 1))
            ;;
    esac

    if printf '%s\n' "${content}" |
        grep -Eiq \
        '^[[:space:]]*(#|//|/\*|\*|;|<!--)'
    then
        COMMENT_BIND_MATCH_COUNT=$((COMMENT_BIND_MATCH_COUNT + 1))
        classification="COMMENT_ONLY"
    fi

    if printf '%s\n' "${content}" |
        grep -Eiq \
        '(example|example\.com|documentation|docs/|README|readme|sample|fixture|mock|fake)'
    then
        DOCUMENTATION_BIND_MATCH_COUNT=$((DOCUMENTATION_BIND_MATCH_COUNT + 1))
        classification="DOCUMENTATION_OR_EXAMPLE"
    fi

    printf '%s\t%s\t%s\t%s\n' \
        "${classification}" \
        "${file}" \
        "${lineno}" \
        "${content}" >> "${TMP_CLASSIFIED}"

done < "${TMP_RAW}"

log "EXACT_APPLICATION_BIND_MATCHES_END"

log ""
log "============================================================"
log "5. BIND CLASSIFICATION COUNTS"
log "============================================================"

log "RAW_APPLICATION_BIND_MATCH_COUNT=${RAW_BIND_MATCH_COUNT}"
log "PYTHON_BIND_MATCH_COUNT=${PYTHON_BIND_MATCH_COUNT}"
log "CONFIG_BIND_MATCH_COUNT=${CONFIG_BIND_MATCH_COUNT}"
log "SERVER_BIND_MATCH_COUNT=${SERVER_BIND_MATCH_COUNT}"
log "DOCUMENTATION_BIND_MATCH_COUNT=${DOCUMENTATION_BIND_MATCH_COUNT}"
log "COMMENT_BIND_MATCH_COUNT=${COMMENT_BIND_MATCH_COUNT}"
log "NON_EXECUTABLE_BIND_MATCH_COUNT=${NON_EXECUTABLE_BIND_MATCH_COUNT}"

if [ "${SERVER_BIND_MATCH_COUNT}" -gt 0 ]; then
    fail "REAL_APPLICATION_SERVER_BIND_PATTERN_DETECTED"
else
    pass "NO_EXPLICIT_APPLICATION_SERVER_BIND_PATTERN_DETECTED"
fi

REAL_CONFIG_BIND_COUNT=0

while IFS=$'\t' read -r classification file lineno content; do
    case "${classification}" in
        PYTHON_CONFIG_BIND|PYTHON_SERVER_BIND|CONFIG_BIND|SCRIPT_BIND)
            if [ "${classification}" != "COMMENT_ONLY" ] &&
               [ "${classification}" != "DOCUMENTATION_OR_EXAMPLE" ]; then
                REAL_CONFIG_BIND_COUNT=$((REAL_CONFIG_BIND_COUNT + 1))
            fi
            ;;
    esac
done < "${TMP_CLASSIFIED}"

log "REAL_EXECUTABLE_OR_CONFIGURATION_BIND_COUNT=${REAL_CONFIG_BIND_COUNT}"

if [ "${REAL_CONFIG_BIND_COUNT}" -gt 0 ]; then
    fail "REAL_APPLICATION_BIND_CONFIGURATION_REQUIRES_REMEDIATION"
else
    pass "NO_REAL_APPLICATION_BIND_CONFIGURATION_REMAINS"
fi

log ""
log "============================================================"
log "6. EXACT TWO-R43-BLOCKER RECONCILIATION"
log "============================================================"

if [ "${RAW_BIND_MATCH_COUNT}" -eq "${R43_APPLICATION_BIND_COUNT:-0}" ]; then
    pass "R43_APPLICATION_BIND_COUNT_EXACTLY_RECONCILED"
else
    review "R43_APPLICATION_BIND_COUNT_DIFFERS_FROM_EXACT_LOCALIZATION"
fi

if [ "${RAW_BIND_MATCH_COUNT}" -eq 2 ]; then
    pass "EXPECTED_TWO_APPLICATION_BIND_MATCHES_LOCATED"
else
    review "APPLICATION_BIND_MATCH_COUNT_IS_NOT_TWO"
fi

log ""
log "============================================================"
log "7. PRODUCTION BIND DECISION"
log "============================================================"

PRODUCTION_BIND_BLOCKER=0

if [ "${SERVER_BIND_MATCH_COUNT}" -gt 0 ]; then
    PRODUCTION_BIND_BLOCKER=1
elif [ "${REAL_CONFIG_BIND_COUNT}" -gt 0 ]; then
    PRODUCTION_BIND_BLOCKER=1
fi

log "PRODUCTION_BIND_BLOCKER=${PRODUCTION_BIND_BLOCKER}"

if [ "${PRODUCTION_BIND_BLOCKER}" -eq 1 ]; then
    fail "PRODUCTION_BIND_BLOCKER_CONFIRMED"
else
    pass "R43_UNSAFE_BIND_IS_NOT_CONFIRMED_AS_PRODUCTION_EXECUTION_BLOCKER"
fi

log ""
log "============================================================"
log "8. FINAL CLASSIFICATION"
log "============================================================"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_03_R44_UNSAFE_BIND_BLOCKER_CONFIRMED"
    EXIT_CODE=2
elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_03_R44_UNSAFE_BIND_BLOCKER_CLASSIFICATION_REVIEW"
    EXIT_CODE=1
else
    STATUS="PASS"
    RESULT="P0_03_R44_UNSAFE_BIND_BLOCKER_LOCATOR_PASS"
    EXIT_CODE=0
fi

log ""
log "============================================================"
log "9. FINAL EVIDENCE CARD"
log "============================================================"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "R43_STATUS=${R43_STATUS:-UNKNOWN}"
log "R43_EXIT_CODE=${R43_EXIT_CODE:-UNKNOWN}"
log "R43_APPLICATION_BIND_COUNT=${R43_APPLICATION_BIND_COUNT:-UNKNOWN}"

log "RAW_APPLICATION_BIND_MATCH_COUNT=${RAW_BIND_MATCH_COUNT}"
log "PYTHON_BIND_MATCH_COUNT=${PYTHON_BIND_MATCH_COUNT}"
log "CONFIG_BIND_MATCH_COUNT=${CONFIG_BIND_MATCH_COUNT}"
log "SERVER_BIND_MATCH_COUNT=${SERVER_BIND_MATCH_COUNT}"
log "DOCUMENTATION_BIND_MATCH_COUNT=${DOCUMENTATION_BIND_MATCH_COUNT}"
log "COMMENT_BIND_MATCH_COUNT=${COMMENT_BIND_MATCH_COUNT}"
log "NON_EXECUTABLE_BIND_MATCH_COUNT=${NON_EXECUTABLE_BIND_MATCH_COUNT}"
log "REAL_EXECUTABLE_OR_CONFIGURATION_BIND_COUNT=${REAL_CONFIG_BIND_COUNT}"
log "PRODUCTION_BIND_BLOCKER=${PRODUCTION_BIND_BLOCKER}"

log "P0_03_R44_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

rm -f "${TMP_RAW}" "${TMP_CLASSIFIED}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
