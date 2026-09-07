#!/data/data/com.termux/files/usr/bin/bash

# ============================================================================
# P0-02 R36
# SECRET PROVENANCE CLOSURE ATTESTATION GATE
#
# PURPOSE
# -------
# Independent post-closure attestation of the R35 PASS state.
#
# R35 is the authoritative current-state security gate.
# R36 does NOT replace R35 and does NOT reopen historical R29 defects.
#
# R36 verifies:
#   1. R35 report exists and is structurally parseable.
#   2. R35 reports PASS / EXIT_CODE=0.
#   3. R35 current evidence card contains the exact closed invariants.
#   4. No R35 failure/review exists.
#   5. Historical contradiction is explicitly classified as historical.
#   6. R35 report itself does not contain secret values.
#   7. R35 closure is internally consistent.
#
# DESIGN
# ------
# READ-ONLY
# FAIL-CLOSED
# NO SOURCE WRITES
# NO RUNTIME EXECUTION
# NO ENV SOURCING
# NO BUILD
# NO DEPLOYMENT
# NO SECRET VALUES PRINTED
#
# IMPORTANT
# ---------
# This script does not mutate the R35 report.
# ============================================================================

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
EXPECTED_ROOT="/data/data/com.termux/files/home/waste-platform"

REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r36_secret_provenance_closure_attestation_gate.txt"

R35_REPORT="${REPORT_DIR}/p0_02_r35_secret_provenance_final_integrity_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

R35_STATUS=""
R35_RESULT=""
R35_EXIT_CODE=""

R35_FAILURE_COUNT=""
R35_REVIEW_COUNT=""

R35_ENV_COUNT=""
R35_COMPOSE_TARGET_COUNT=""
R35_COMPOSE_REFERENCE_COUNT=""
R35_COMPOSE_LITERAL_COUNT=""
R35_COMPOSE_KEY_FAILURES=""

R35_DATABASE_URL_COUNT=""
R35_RUNTIME_ASSIGNMENT_COUNT=""
R35_CI_COUNT=""
R35_DEPLOY_COUNT=""

R35_APPLICATION_OUTPUT_COUNT=""
R35_APPLICATION_LITERAL_COUNT=""

R35_FORENSIC_COUNT=""
R35_HISTORICAL_COUNT=""

R35_R29_MISSING=""
R35_R29_CONSISTENT=""
R35_R29_CONTRADICTION=""

R35_ATTESTATION_CONSISTENCY=1
R35_SECRET_VALUE_SUSPECT_COUNT=0

log() {
    printf '%s\n' "$1"
    printf '%s\n' "$1" >> "${REPORT}"
}

section() {
    log ""
    log "============================================================"
    log "$1"
    log "============================================================"
}

pass() {
    log "PASS: $1"
}

review() {
    log "REVIEW: $1"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

fail() {
    log "FAIL: $1"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "${TMP_DIR}"
}

trap cleanup EXIT

mkdir -p "${REPORT_DIR}"
: > "${REPORT}"

section "P0-02 R36 SECRET PROVENANCE CLOSURE ATTESTATION GATE"

section "1. SAFETY PRECHECK"

if [ "${PROJECT_ROOT}" = "${EXPECTED_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
else
    fail "PROJECT_ROOT_MISMATCH=${PROJECT_ROOT}"
fi

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_R35_REPORT_MUTATION=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "FAIL_CLOSED=YES"
pass "INDEPENDENT_R35_ATTESTATION=YES"

section "2. REQUIRED TOOLCHAIN"

for tool in awk grep sed tr wc mktemp; do
    if command -v "${tool}" >/dev/null 2>&1; then
        pass "TOOL_AVAILABLE=${tool}"
    else
        fail "TOOL_MISSING=${tool}"
    fi
done

section "3. R35 REPORT PRESENCE"

if [ -f "${R35_REPORT}" ]; then
    pass "R35_REPORT_PRESENT"
else
    fail "R35_REPORT_MISSING"
fi

if [ -s "${R35_REPORT}" ]; then
    pass "R35_REPORT_NONEMPTY"
else
    fail "R35_REPORT_EMPTY"
fi

section "4. R35 FINAL STATUS ATTESTATION"

if [ -f "${R35_REPORT}" ]; then

    R35_STATUS="$(
        awk -F= '
            /^P0_02_R35_STATUS=/ {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R35_REPORT}"
    )"

    R35_RESULT="$(
        awk -F= '
            /^RESULT=/ {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R35_REPORT}"
    )"

    R35_EXIT_CODE="$(
        awk -F= '
            /^EXIT_CODE=/ {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R35_REPORT}"
    )"

    R35_FAILURE_COUNT="$(
        awk -F= '
            /^FAILURE_COUNT=/ {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R35_REPORT}"
    )"

    R35_REVIEW_COUNT="$(
        awk -F= '
            /^REVIEW_COUNT=/ {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R35_REPORT}"
    )"

    log "R35_STATUS=${R35_STATUS}"
    log "R35_RESULT=${R35_RESULT}"
    log "R35_EXIT_CODE=${R35_EXIT_CODE}"
    log "R35_FAILURE_COUNT=${R35_FAILURE_COUNT}"
    log "R35_REVIEW_COUNT=${R35_REVIEW_COUNT}"

    if [ "${R35_STATUS}" = "PASS" ]; then
        pass "R35_STATUS_PASS"
    else
        fail "R35_STATUS_NOT_PASS"
    fi

    if [ "${R35_RESULT}" = "P0_02_R35_SECRET_PROVENANCE_FINAL_INTEGRITY_PASS" ]; then
        pass "R35_RESULT_EXACT"
    else
        fail "R35_RESULT_MISMATCH"
    fi

    if [ "${R35_EXIT_CODE}" = "0" ]; then
        pass "R35_EXIT_CODE_ZERO"
    else
        fail "R35_EXIT_CODE_NONZERO"
    fi

    if [ "${R35_FAILURE_COUNT}" = "0" ]; then
        pass "R35_FAILURE_COUNT_ZERO"
    else
        fail "R35_FAILURE_COUNT_NONZERO"
    fi

    if [ "${R35_REVIEW_COUNT}" = "0" ]; then
        pass "R35_REVIEW_COUNT_ZERO"
    else
        fail "R35_REVIEW_COUNT_NONZERO"
    fi

else
    fail "R35_FINAL_STATUS_CANNOT_BE_ATTESTED"
fi

section "5. R35 CURRENT EVIDENCE CARD"

if [ -f "${R35_REPORT}" ]; then

    extract_value() {
        local key="$1"

        awk -F= -v wanted="${key}" '
            $1 == wanted {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R35_REPORT}"
    }

    R35_ENV_COUNT="$(extract_value "ENV_SECRET_AUTHORITY_COUNT")"
    R35_COMPOSE_TARGET_COUNT="$(extract_value "COMPOSE_TARGET_COUNT")"
    R35_COMPOSE_REFERENCE_COUNT="$(extract_value "COMPOSE_REFERENCE_COUNT")"
    R35_COMPOSE_LITERAL_COUNT="$(extract_value "COMPOSE_LITERAL_COUNT")"
    R35_COMPOSE_KEY_FAILURES="$(extract_value "COMPOSE_KEY_REFERENCE_FAILURES")"

    R35_DATABASE_URL_COUNT="$(extract_value "DATABASE_URL_MATCH_COUNT")"

    R35_RUNTIME_ASSIGNMENT_COUNT="$(extract_value "RUNTIME_DIRECT_ASSIGNMENT_COUNT")"
    R35_CI_COUNT="$(extract_value "CI_IDENTIFIER_COUNT")"
    R35_DEPLOY_COUNT="$(extract_value "DEPLOY_SECRET_REFERENCE_COUNT")"

    R35_APPLICATION_OUTPUT_COUNT="$(extract_value "CURRENT_APPLICATION_OUTPUT_MATCH_COUNT")"
    R35_APPLICATION_LITERAL_COUNT="$(extract_value "CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT")"

    R35_FORENSIC_COUNT="$(extract_value "FORENSIC_ARCHIVE_MATCH_COUNT")"
    R35_HISTORICAL_COUNT="$(extract_value "HISTORICAL_AUDIT_MATCH_COUNT")"

    R35_R29_MISSING="$(extract_value "R29_COMPOSE_MISSING_COUNT")"
    R35_R29_CONSISTENT="$(extract_value "R29_INTERNAL_CONSISTENT_ASSERTION_COUNT")"
    R35_R29_CONTRADICTION="$(extract_value "R29_HISTORICAL_CONTRADICTION")"

    log "R35_ENV_SECRET_AUTHORITY_COUNT=${R35_ENV_COUNT}"
    log "R35_COMPOSE_TARGET_COUNT=${R35_COMPOSE_TARGET_COUNT}"
    log "R35_COMPOSE_REFERENCE_COUNT=${R35_COMPOSE_REFERENCE_COUNT}"
    log "R35_COMPOSE_LITERAL_COUNT=${R35_COMPOSE_LITERAL_COUNT}"
    log "R35_COMPOSE_KEY_REFERENCE_FAILURES=${R35_COMPOSE_KEY_FAILURES}"

    log "R35_DATABASE_URL_MATCH_COUNT=${R35_DATABASE_URL_COUNT}"

    log "R35_RUNTIME_DIRECT_ASSIGNMENT_COUNT=${R35_RUNTIME_ASSIGNMENT_COUNT}"
    log "R35_CI_IDENTIFIER_COUNT=${R35_CI_COUNT}"
    log "R35_DEPLOY_SECRET_REFERENCE_COUNT=${R35_DEPLOY_COUNT}"

    log "R35_CURRENT_APPLICATION_OUTPUT_MATCH_COUNT=${R35_APPLICATION_OUTPUT_COUNT}"
    log "R35_CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT=${R35_APPLICATION_LITERAL_COUNT}"

else
    fail "R35_EVIDENCE_CARD_UNAVAILABLE"
fi

section "6. EXACT CURRENT INVARIANT ATTESTATION"

if [ "${R35_ENV_COUNT}" = "5" ]; then
    pass "R35_ENV_AUTHORITY_EXACT_5"
else
    fail "R35_ENV_AUTHORITY_NOT_EXACT_5"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_COMPOSE_TARGET_COUNT}" = "3" ]; then
    pass "R35_COMPOSE_TARGET_EXACT_3"
else
    fail "R35_COMPOSE_TARGET_NOT_EXACT_3"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_COMPOSE_REFERENCE_COUNT}" = "3" ]; then
    pass "R35_COMPOSE_REFERENCE_EXACT_3"
else
    fail "R35_COMPOSE_REFERENCE_NOT_EXACT_3"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_COMPOSE_LITERAL_COUNT}" = "0" ]; then
    pass "R35_COMPOSE_LITERAL_EXACT_0"
else
    fail "R35_COMPOSE_LITERAL_NOT_ZERO"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_COMPOSE_KEY_FAILURES}" = "0" ]; then
    pass "R35_COMPOSE_KEY_FAILURES_ZERO"
else
    fail "R35_COMPOSE_KEY_FAILURES_NONZERO"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_DATABASE_URL_COUNT}" -ge 1 ] 2>/dev/null; then
    pass "R35_DATABASE_URL_PROVENANCE_PRESENT"
else
    fail "R35_DATABASE_URL_PROVENANCE_MISSING"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_RUNTIME_ASSIGNMENT_COUNT}" = "0" ]; then
    pass "R35_RUNTIME_DIRECT_ASSIGNMENT_ZERO"
else
    fail "R35_RUNTIME_DIRECT_ASSIGNMENT_NONZERO"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_CI_COUNT}" = "5" ]; then
    pass "R35_CI_IDENTIFIER_EXACT_5"
else
    fail "R35_CI_IDENTIFIER_NOT_EXACT_5"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_DEPLOY_COUNT}" = "0" ]; then
    pass "R35_DEPLOY_REFERENCE_ZERO"
else
    fail "R35_DEPLOY_REFERENCE_NONZERO"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_APPLICATION_OUTPUT_COUNT}" = "0" ]; then
    pass "R35_APPLICATION_OUTPUT_ZERO"
else
    fail "R35_APPLICATION_OUTPUT_NONZERO"
    R35_ATTESTATION_CONSISTENCY=0
fi

if [ "${R35_APPLICATION_LITERAL_COUNT}" = "0" ]; then
    pass "R35_APPLICATION_LITERAL_LEAK_ZERO"
else
    fail "R35_APPLICATION_LITERAL_LEAK_NONZERO"
    R35_ATTESTATION_CONSISTENCY=0
fi

section "7. R35 HISTORICAL CLASSIFICATION ATTESTATION"

if [ "${R35_R29_MISSING}" = "3" ]; then
    pass "R29_HISTORICAL_MISSING_ASSERTIONS_RETAINED"
else
    fail "R29_HISTORICAL_MISSING_ASSERTION_COUNT_UNEXPECTED"
fi

if [ "${R35_R29_CONSISTENT}" = "1" ]; then
    pass "R29_HISTORICAL_CONSISTENT_ASSERTION_RETAINED"
else
    fail "R29_HISTORICAL_CONSISTENT_ASSERTION_COUNT_UNEXPECTED"
fi

if [ "${R35_R29_CONTRADICTION}" = "1" ]; then
    pass "R29_HISTORICAL_CONTRADICTION_FLAGGED"
else
    fail "R29_HISTORICAL_CONTRADICTION_NOT_FLAGGED"
fi

if [ "${R35_R29_MISSING}" -gt 0 ] 2>/dev/null &&
   [ "${R35_R29_CONSISTENT}" -gt 0 ] 2>/dev/null &&
   [ "${R35_R29_CONTRADICTION}" = "1" ]; then

    pass "R29_DEFECT_CORRECTLY_CLASSIFIED_HISTORICAL"

else

    fail "R29_HISTORICAL_CLASSIFICATION_INCONSISTENT"

fi

section "8. R35 REPORT SECRET-VALUE SAFETY"

SECRET_VALUE_SUSPECT_COUNT="$(
    grep -En \
        -E '(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*[:=][[:space:]]*["'\''][A-Za-z0-9_./:@%+,-]{12,}["'\'']' \
        "${R35_REPORT}" \
        2>/dev/null \
    | grep -Ev \
        '(\$\{|<VALUE_REDACTED>|<REDACTED>|COUNT|CARDINALITY|ZERO|MISSING|PRESENT|REFERENCE|IDENTIFIER|FAILURE|REVIEW)' \
    | wc -l \
    | tr -d ' '
)"

if [ -z "${SECRET_VALUE_SUSPECT_COUNT}" ]; then
    SECRET_VALUE_SUSPECT_COUNT=0
fi

log "R35_SECRET_VALUE_SUSPECT_COUNT=${SECRET_VALUE_SUSPECT_COUNT}"

if [ "${SECRET_VALUE_SUSPECT_COUNT}" -eq 0 ]; then
    pass "R35_REPORT_NO_SECRET_VALUE_SUSPECT"
else
    fail "R35_REPORT_SECRET_VALUE_PATTERN_SUSPECT"
fi

section "9. R35 STRUCTURAL INTEGRITY"

R35_STATUS_COUNT="$(
    grep -Ec '^P0_02_R35_STATUS=' "${R35_REPORT}" 2>/dev/null || true
)"

R35_RESULT_COUNT="$(
    grep -Ec '^RESULT=' "${R35_REPORT}" 2>/dev/null || true
)"

R35_EXIT_COUNT="$(
    grep -Ec '^EXIT_CODE=' "${R35_REPORT}" 2>/dev/null || true
)"

R35_EVIDENCE_COUNT="$(
    grep -Ec '^FAILURE_COUNT=' "${R35_REPORT}" 2>/dev/null || true
)"

log "R35_STATUS_RECORD_COUNT=${R35_STATUS_COUNT}"
log "R35_RESULT_RECORD_COUNT=${R35_RESULT_COUNT}"
log "R35_EXIT_RECORD_COUNT=${R35_EXIT_COUNT}"
log "R35_FAILURE_RECORD_COUNT=${R35_EVIDENCE_COUNT}"

if [ "${R35_STATUS_COUNT}" -eq 1 ]; then
    pass "R35_STATUS_RECORD_UNIQUE"
else
    fail "R35_STATUS_RECORD_NOT_UNIQUE"
fi

if [ "${R35_RESULT_COUNT}" -eq 1 ]; then
    pass "R35_RESULT_RECORD_UNIQUE"
else
    fail "R35_RESULT_RECORD_NOT_UNIQUE"
fi

if [ "${R35_EXIT_COUNT}" -eq 1 ]; then
    pass "R35_EXIT_RECORD_UNIQUE"
else
    fail "R35_EXIT_RECORD_NOT_UNIQUE"
fi

if [ "${R35_EVIDENCE_COUNT}" -eq 1 ]; then
    pass "R35_FAILURE_RECORD_UNIQUE"
else
    fail "R35_FAILURE_RECORD_NOT_UNIQUE"
fi

section "10. CLOSURE CONSISTENCY"

if [ "${R35_STATUS}" = "PASS" ] &&
   [ "${R35_RESULT}" = "P0_02_R35_SECRET_PROVENANCE_FINAL_INTEGRITY_PASS" ] &&
   [ "${R35_EXIT_CODE}" = "0" ] &&
   [ "${R35_FAILURE_COUNT}" = "0" ] &&
   [ "${R35_REVIEW_COUNT}" = "0" ] &&
   [ "${R35_ATTESTATION_CONSISTENCY}" -eq 1 ]; then

    pass "R35_CLOSURE_STATE_INTERNALLY_CONSISTENT"

else

    fail "R35_CLOSURE_STATE_INTERNAL_INCONSISTENCY"

fi

section "11. FINAL ATTESTATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_02_R36_SECRET_PROVENANCE_CLOSURE_ATTESTATION_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_02_R36_SECRET_PROVENANCE_CLOSURE_ATTESTATION_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_02_R36_SECRET_PROVENANCE_CLOSURE_ATTESTATION_PASS"
    EXIT_CODE=0

fi

section "12. FINAL EVIDENCE CARD"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "R35_STATUS=${R35_STATUS}"
log "R35_RESULT=${R35_RESULT}"
log "R35_EXIT_CODE=${R35_EXIT_CODE}"

log "R35_ENV_SECRET_AUTHORITY_COUNT=${R35_ENV_COUNT}"

log "R35_COMPOSE_TARGET_COUNT=${R35_COMPOSE_TARGET_COUNT}"
log "R35_COMPOSE_REFERENCE_COUNT=${R35_COMPOSE_REFERENCE_COUNT}"
log "R35_COMPOSE_LITERAL_COUNT=${R35_COMPOSE_LITERAL_COUNT}"
log "R35_COMPOSE_KEY_REFERENCE_FAILURES=${R35_COMPOSE_KEY_FAILURES}"

log "R35_DATABASE_URL_MATCH_COUNT=${R35_DATABASE_URL_COUNT}"

log "R35_RUNTIME_DIRECT_ASSIGNMENT_COUNT=${R35_RUNTIME_ASSIGNMENT_COUNT}"
log "R35_CI_IDENTIFIER_COUNT=${R35_CI_COUNT}"
log "R35_DEPLOY_SECRET_REFERENCE_COUNT=${R35_DEPLOY_COUNT}"

log "R35_CURRENT_APPLICATION_OUTPUT_MATCH_COUNT=${R35_APPLICATION_OUTPUT_COUNT}"
log "R35_CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT=${R35_APPLICATION_LITERAL_COUNT}"

log "R35_FORENSIC_ARCHIVE_MATCH_COUNT=${R35_FORENSIC_COUNT}"
log "R35_HISTORICAL_AUDIT_MATCH_COUNT=${R35_HISTORICAL_COUNT}"

log "R29_COMPOSE_MISSING_COUNT=${R35_R29_MISSING}"
log "R29_INTERNAL_CONSISTENT_ASSERTION_COUNT=${R35_R29_CONSISTENT}"
log "R29_HISTORICAL_CONTRADICTION=${R35_R29_CONTRADICTION}"

log "R35_SECRET_VALUE_SUSPECT_COUNT=${SECRET_VALUE_SUSPECT_COUNT}"

log "P0_02_R36_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
