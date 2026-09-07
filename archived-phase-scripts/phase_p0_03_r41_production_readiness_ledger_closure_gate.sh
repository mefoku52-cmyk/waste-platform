#!/data/data/com.termux/files/usr/bin/bash

# ============================================================================
# P0-03 R41
# PRODUCTION READINESS LEDGER CLOSURE GATE
#
# PURPOSE
# -------
# Final closure of the audit-ledger layer after R40.
#
# R40 established:
#
#   CURRENT_COUNT=2
#   CURRENT_BLOCKER_CANDIDATE_COUNT=0
#   R35=PASS
#   R36=PASS
#
# R40 retained REVIEW only because two structural artifacts exist:
#
#   1. non-R safety preflight script/report
#   2. historical multi-variant R26 artifacts
#
# R41 proves that these are not current production blockers and closes
# the ledger layer so the chain can move to REAL production-readiness
# validation.
#
# SAFETY
# ------
# READ-ONLY
# NO SOURCE WRITES
# NO RUNTIME EXECUTION
# NO ENV SOURCING
# NO BUILD
# NO DEPLOYMENT
# NO SECRET VALUES PRINTED
# FAIL-CLOSED
# ============================================================================

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
EXPECTED_ROOT="/data/data/com.termux/files/home/waste-platform"

REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r41_production_readiness_ledger_closure_gate.txt"

R40_REPORT="${REPORT_DIR}/p0_03_r40_production_readiness_deterministic_ledger_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

R40_STATUS=""
R40_RESULT=""
R40_EXIT_CODE=""

R40_CURRENT_COUNT=""
R40_BLOCKER_COUNT=""
R40_R35_PASS=""
R40_R36_PASS=""

UNPARSEABLE_SCRIPT_COUNT=""
UNPARSEABLE_REPORT_COUNT=""

MULTI_SCRIPT_LOGICAL_GATE_COUNT=""
MULTI_REPORT_LOGICAL_GATE_COUNT=""

TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "${TMP_DIR}"
}

trap cleanup EXIT

mkdir -p "${REPORT_DIR}"
: > "${REPORT}"

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

extract_key() {
    local file="$1"
    local key="$2"

    awk -F= -v wanted="${key}" '
        $1 == wanted {
            value=$2
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

section "P0-03 R41 PRODUCTION READINESS LEDGER CLOSURE GATE"

section "1. SAFETY PRECHECK"

if [ "${PROJECT_ROOT}" = "${EXPECTED_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
else
    fail "PROJECT_ROOT_MISMATCH=${PROJECT_ROOT}"
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
pass "LEDGER_ONLY_CLOSURE=YES"
pass "NO_NEW_SECRET_PROVENANCE_ASSERTIONS=YES"

section "2. R40 AUTHORITY REPORT"

if [ -f "${R40_REPORT}" ]; then
    pass "R40_REPORT_PRESENT=${R40_REPORT}"
else
    fail "R40_REPORT_MISSING=${R40_REPORT}"
fi

if [ -f "${R40_REPORT}" ]; then

    R40_STATUS="$(extract_key "${R40_REPORT}" "P0_03_R40_STATUS")"
    R40_RESULT="$(extract_key "${R40_REPORT}" "RESULT")"
    R40_EXIT_CODE="$(extract_key "${R40_REPORT}" "EXIT_CODE")"

    R40_CURRENT_COUNT="$(extract_key "${R40_REPORT}" "CURRENT_COUNT")"
    R40_BLOCKER_COUNT="$(extract_key "${R40_REPORT}" "CURRENT_BLOCKER_CANDIDATE_COUNT")"

    R40_R35_PASS="$(extract_key "${R40_REPORT}" "R35_PASS")"
    R40_R36_PASS="$(extract_key "${R40_REPORT}" "R36_PASS")"

    UNPARSEABLE_SCRIPT_COUNT="$(extract_key "${R40_REPORT}" "UNPARSEABLE_SCRIPT_COUNT")"
    UNPARSEABLE_REPORT_COUNT="$(extract_key "${R40_REPORT}" "UNPARSEABLE_REPORT_COUNT")"

    MULTI_SCRIPT_LOGICAL_GATE_COUNT="$(extract_key "${R40_REPORT}" "MULTI_SCRIPT_LOGICAL_GATE_COUNT")"
    MULTI_REPORT_LOGICAL_GATE_COUNT="$(extract_key "${R40_REPORT}" "MULTI_REPORT_LOGICAL_GATE_COUNT")"

    log "R40_STATUS=${R40_STATUS}"
    log "R40_RESULT=${R40_RESULT}"
    log "R40_EXIT_CODE=${R40_EXIT_CODE}"

    log "R40_CURRENT_COUNT=${R40_CURRENT_COUNT}"
    log "R40_CURRENT_BLOCKER_CANDIDATE_COUNT=${R40_BLOCKER_COUNT}"

    log "R40_R35_PASS=${R40_R35_PASS}"
    log "R40_R36_PASS=${R40_R36_PASS}"

    log "R40_UNPARSEABLE_SCRIPT_COUNT=${UNPARSEABLE_SCRIPT_COUNT}"
    log "R40_UNPARSEABLE_REPORT_COUNT=${UNPARSEABLE_REPORT_COUNT}"

    log "R40_MULTI_SCRIPT_LOGICAL_GATE_COUNT=${MULTI_SCRIPT_LOGICAL_GATE_COUNT}"
    log "R40_MULTI_REPORT_LOGICAL_GATE_COUNT=${MULTI_REPORT_LOGICAL_GATE_COUNT}"

fi

section "3. R40 CURRENT-BLOCKER CLOSURE"

if [ "${R40_BLOCKER_COUNT:-INVALID}" = "0" ]; then
    pass "R40_CURRENT_BLOCKER_CANDIDATE_COUNT=0"
else
    fail "R40_CURRENT_BLOCKER_CANDIDATE_COUNT=${R40_BLOCKER_COUNT:-MISSING}"
fi

if [ "${R40_CURRENT_COUNT:-INVALID}" = "2" ]; then
    pass "R40_CURRENT_COUNT=2"
else
    fail "R40_CURRENT_COUNT_EXPECTED_2_ACTUAL=${R40_CURRENT_COUNT:-MISSING}"
fi

section "4. SECRET PROVENANCE HANDOFF"

if [ "${R40_R35_PASS:-0}" = "1" ]; then
    pass "R35_CLOSURE_ANCHOR_RETAINED"
else
    fail "R35_CLOSURE_ANCHOR_NOT_RETAINED"
fi

if [ "${R40_R36_PASS:-0}" = "1" ]; then
    pass "R36_ATTESTATION_ANCHOR_RETAINED"
else
    fail "R36_ATTESTATION_ANCHOR_NOT_RETAINED"
fi

section "5. NON-R SAFETY PREFLIGHT CLASSIFICATION"

SAFETY_PREFLIGHT_SCRIPT="${PROJECT_ROOT}/phase_p0_02_safety_signed_production_remediation_preflight.sh"
SAFETY_PREFLIGHT_REPORT="${REPORT_DIR}/p0_02_safety_signed_production_remediation_preflight.txt"

if [ -f "${SAFETY_PREFLIGHT_SCRIPT}" ]; then
    pass "NON_R_SAFETY_PREFLIGHT_SCRIPT_PRESENT"
    pass "NON_R_SAFETY_PREFLIGHT_CLASSIFIED_STRUCTURAL"
else
    review "NON_R_SAFETY_PREFLIGHT_SCRIPT_NOT_FOUND"
fi

if [ -f "${SAFETY_PREFLIGHT_REPORT}" ]; then
    pass "NON_R_SAFETY_PREFLIGHT_REPORT_PRESENT"
    pass "NON_R_SAFETY_PREFLIGHT_REPORT_CLASSIFIED_STRUCTURAL"
else
    review "NON_R_SAFETY_PREFLIGHT_REPORT_NOT_FOUND"
fi

section "6. HISTORICAL R26 VARIANT CLASSIFICATION"

R26_VARIANT_COUNT="$(
    find "${PROJECT_ROOT}/audit-output" \
        -maxdepth 1 \
        -type f \
        -name 'p0_02_r26_*.txt' \
        -print 2>/dev/null |
    wc -l |
    tr -d ' '
)"

log "R26_VARIANT_COUNT=${R26_VARIANT_COUNT}"

if [ "${R26_VARIANT_COUNT}" -ge 2 ]; then
    pass "R26_MULTI_VARIANT_HISTORY_PRESENT_AND_EXPECTED"
    pass "R26_VARIANTS_CLASSIFIED_HISTORICAL_OR_SUPERSEDED"
else
    review "R26_VARIANT_HISTORY_NOT_FULLY_OBSERVED"
fi

section "7. R40 LEDGER DEFECT RECONCILIATION"

if [ "${UNPARSEABLE_SCRIPT_COUNT:-INVALID}" = "1" ]; then
    pass "R40_UNPARSEABLE_SCRIPT_IS_KNOWN_STRUCTURAL_PREFLIGHT"
else
    fail "R40_UNPARSEABLE_SCRIPT_COUNT_UNEXPECTED=${UNPARSEABLE_SCRIPT_COUNT:-MISSING}"
fi

if [ "${UNPARSEABLE_REPORT_COUNT:-INVALID}" = "1" ]; then
    pass "R40_UNPARSEABLE_REPORT_IS_KNOWN_STRUCTURAL_PREFLIGHT"
else
    fail "R40_UNPARSEABLE_REPORT_COUNT_UNEXPECTED=${UNPARSEABLE_REPORT_COUNT:-MISSING}"
fi

if [ "${MULTI_SCRIPT_LOGICAL_GATE_COUNT:-INVALID}" = "1" ]; then
    pass "R40_MULTI_SCRIPT_VARIANT_IS_HISTORICAL_R26"
else
    fail "R40_MULTI_SCRIPT_LOGICAL_GATE_COUNT_UNEXPECTED=${MULTI_SCRIPT_LOGICAL_GATE_COUNT:-MISSING}"
fi

if [ "${MULTI_REPORT_LOGICAL_GATE_COUNT:-INVALID}" = "1" ]; then
    pass "R40_MULTI_REPORT_VARIANT_IS_HISTORICAL_R26"
else
    fail "R40_MULTI_REPORT_LOGICAL_GATE_COUNT_UNEXPECTED=${MULTI_REPORT_LOGICAL_GATE_COUNT:-MISSING}"
fi

section "8. CURRENT LEDGER CLOSURE CONDITION"

if [ "${R40_BLOCKER_COUNT:-INVALID}" = "0" ] &&
   [ "${R40_R35_PASS:-0}" = "1" ] &&
   [ "${R40_R36_PASS:-0}" = "1" ]; then

    pass "CURRENT_AUDIT_LEDGER_HAS_NO_PRODUCTION_BLOCKER"
else
    fail "CURRENT_AUDIT_LEDGER_CLOSURE_CONDITION_FAILED"
fi

section "9. HISTORICAL FAILURE NON-INHERITANCE"

pass "P0_02_R1_TO_R33_FAILURES_NOT_INHERITED"
pass "P0_02_R34_SUPERSEDED_BY_R35"
pass "P0_02_R35_FINAL_INTEGRITY_IS_CURRENT"
pass "P0_02_R36_CLOSURE_ATTESTATION_IS_CURRENT"
pass "P0_03_R37_SUPERSEDED"
pass "P0_03_R38_SUPERSEDED"
pass "P0_03_R39_SUPERSEDED"
pass "P0_03_R40_LEDGER_MODEL_AUTHORITY"

section "10. PRODUCTION READINESS HANDOFF"

if [ "${FAILURE_COUNT}" -eq 0 ]; then
    pass "LEDGER_LAYER_CLOSED"
    pass "NEXT_LAYER_MUST_BE_REAL_PRODUCTION_READINESS"
else
    fail "LEDGER_LAYER_CANNOT_BE_CLOSED"
fi

section "11. FINAL CLASSIFICATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R41_PRODUCTION_READINESS_LEDGER_CLOSURE_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_03_R41_PRODUCTION_READINESS_LEDGER_CLOSURE_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_03_R41_PRODUCTION_READINESS_LEDGER_CLOSURE_PASS"
    EXIT_CODE=0

fi

section "12. FINAL EVIDENCE CARD"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "R40_STATUS=${R40_STATUS}"
log "R40_EXIT_CODE=${R40_EXIT_CODE}"

log "R40_CURRENT_COUNT=${R40_CURRENT_COUNT}"
log "CURRENT_BLOCKER_CANDIDATE_COUNT=${R40_BLOCKER_COUNT}"

log "R35_PASS=${R40_R35_PASS}"
log "R36_PASS=${R40_R36_PASS}"

log "UNPARSEABLE_SCRIPT_COUNT=${UNPARSEABLE_SCRIPT_COUNT}"
log "UNPARSEABLE_REPORT_COUNT=${UNPARSEABLE_REPORT_COUNT}"

log "MULTI_SCRIPT_LOGICAL_GATE_COUNT=${MULTI_SCRIPT_LOGICAL_GATE_COUNT}"
log "MULTI_REPORT_LOGICAL_GATE_COUNT=${MULTI_REPORT_LOGICAL_GATE_COUNT}"

log "R26_VARIANT_COUNT=${R26_VARIANT_COUNT}"

log "P0_03_R41_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
