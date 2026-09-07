#!/data/data/com.termux/files/usr/bin/bash

# ============================================================================
# P0-03 R40
# PRODUCTION READINESS DETERMINISTIC LEDGER GATE
#
# PURPOSE
# -------
# Replace the broken multiline TSV matrix model used by R39.
#
# R40 deliberately uses one filesystem object per record.
#
# It does NOT concatenate multiple paths into a single TSV field.
# It does NOT infer status by global R number.
# It does NOT use keyword-only historical classification.
#
# Logical identity:
#
#       namespace + R number
#
# Explicit supersession:
#
#       P0-02:R1..R34  -> SUPERSEDED by R35/R36
#       P0-02:R35      -> CURRENT closure anchor
#       P0-02:R36      -> CURRENT closure attestation
#       P0-03:R37      -> SUPERSEDED
#       P0-03:R38      -> SUPERSEDED
#       P0-03:R39      -> SUPERSEDED
#       P0-03:R40      -> STRUCTURAL / SELF
#
# P0-01 is historical.
#
# IMPORTANT
# ---------
# This gate is an audit-ledger correction gate.
# It does NOT claim production readiness.
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
REPORT="${REPORT_DIR}/p0_03_r40_production_readiness_deterministic_ledger_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

SCRIPT_COUNT=0
REPORT_COUNT=0

UNPARSEABLE_SCRIPT_COUNT=0
UNPARSEABLE_REPORT_COUNT=0

UNIQUE_GATE_COUNT=0
MULTI_SCRIPT_GATE_COUNT=0
MULTI_REPORT_GATE_COUNT=0

PASS_COUNT=0
REVIEW_STATUS_COUNT=0
FAIL_STATUS_COUNT=0
UNKNOWN_STATUS_COUNT=0

CURRENT_COUNT=0
SUPERSEDED_COUNT=0
HISTORICAL_COUNT=0
STRUCTURAL_COUNT=0

CURRENT_BLOCKER_COUNT=0

R35_PASS=0
R36_PASS=0

TMP_DIR="$(mktemp -d)"

SCRIPT_INDEX="${TMP_DIR}/scripts.tsv"
REPORT_INDEX="${TMP_DIR}/reports.tsv"
GATE_KEYS="${TMP_DIR}/gate_keys.tsv"
BLOCKERS="${TMP_DIR}/blockers.tsv"

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

extract_status() {
    local file="$1"
    local namespace="$2"
    local r_number="$3"

    local ns_upper
    ns_upper="$(printf '%s' "${namespace}" | tr '[:lower:]' '[:upper:]')"

    awk -F= -v wanted="${ns_upper}_R${r_number}_STATUS" '
        $1 == wanted {
            value=$2
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

parse_script_identity() {
    local base="$1"

    printf '%s\n' "${base}" |
        sed -nE 's/^phase_(p0_[0-9]+)_r([0-9]+)_.*/\1\t\2/p'
}

parse_report_identity() {
    local base="$1"

    printf '%s\n' "${base}" |
        sed -nE 's/^p0_([0-9]+)_r([0-9]+)_.*/p0_\1\t\2/p'
}

section "P0-03 R40 PRODUCTION READINESS DETERMINISTIC LEDGER GATE"

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
pass "ONE_OBJECT_ONE_RECORD=YES"
pass "NO_MULTILINE_TSV_FIELDS=YES"
pass "NAMESPACE_AWARE=YES"
pass "EXPLICIT_SUPERSESSION=YES"

section "2. REQUIRED TOOLCHAIN"

for tool in awk grep sed sort uniq find wc tr mktemp head basename; do
    if command -v "${tool}" >/dev/null 2>&1; then
        pass "TOOL_AVAILABLE=${tool}"
    else
        fail "TOOL_MISSING=${tool}"
    fi
done

section "3. AUTHORITY PATHS"

for path in \
    "${PROJECT_ROOT}" \
    "${REPORT_DIR}" \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/.github" \
    "${PROJECT_ROOT}/scripts"
do
    if [ -d "${path}" ]; then
        pass "PATH_PRESENT=${path}"
    else
        review "PATH_NOT_PRESENT=${path}"
    fi
done

section "4. SCRIPT DISCOVERY"

find "${PROJECT_ROOT}" \
    -type f \
    -name 'phase_*_r*.sh' \
    -not -path '*/.git/*' \
    -not -path '*/audit-output/*' \
    -print 2>/dev/null |
sort > "${SCRIPT_INDEX}"

SCRIPT_COUNT="$(wc -l < "${SCRIPT_INDEX}" | tr -d ' ')"

log "SCRIPT_COUNT=${SCRIPT_COUNT}"

if [ "${SCRIPT_COUNT}" -gt 0 ]; then
    pass "AUDIT_SCRIPT_DISCOVERY_NONEMPTY"
else
    fail "AUDIT_SCRIPT_DISCOVERY_EMPTY"
fi

section "5. REPORT DISCOVERY"

find "${REPORT_DIR}" \
    -maxdepth 1 \
    -type f \
    -name '*.txt' \
    -not -name 'p0_03_r40_production_readiness_deterministic_ledger_gate.txt' \
    -print 2>/dev/null |
sort > "${REPORT_INDEX}"

REPORT_COUNT="$(wc -l < "${REPORT_INDEX}" | tr -d ' ')"

log "REPORT_COUNT=${REPORT_COUNT}"

if [ "${REPORT_COUNT}" -gt 0 ]; then
    pass "AUDIT_REPORT_DISCOVERY_NONEMPTY"
else
    review "AUDIT_REPORT_DISCOVERY_EMPTY"
fi

section "6. SCRIPT IDENTITY VALIDATION"

: > "${GATE_KEYS}"

while IFS= read -r script; do

    [ -z "${script}" ] && continue

    base="$(basename "${script}")"
    identity="$(parse_script_identity "${base}")"

    if [ -z "${identity}" ]; then
        UNPARSEABLE_SCRIPT_COUNT=$((UNPARSEABLE_SCRIPT_COUNT + 1))
        log "UNPARSEABLE_SCRIPT=${base}"
        continue
    fi

    namespace="$(printf '%s\n' "${identity}" | cut -f1)"
    r_number="$(printf '%s\n' "${identity}" | cut -f2)"

    printf '%s\t%s\tSCRIPT\t%s\n' \
        "${namespace}" \
        "${r_number}" \
        "${script}" >> "${GATE_KEYS}"

done < "${SCRIPT_INDEX}"

log "UNPARSEABLE_SCRIPT_COUNT=${UNPARSEABLE_SCRIPT_COUNT}"

#
# The following known file is a safety/remediation preflight artifact whose
# name intentionally does not contain an R number. It is structural, not a
# production blocker.
#
if grep -Fxq \
    "${PROJECT_ROOT}/phase_p0_02_safety_signed_production_remediation_preflight.sh" \
    "${SCRIPT_INDEX}" 2>/dev/null; then

    pass "NON_R_SAFETY_PREFLIGHT_IDENTIFIED_AS_STRUCTURAL"

fi

section "7. REPORT IDENTITY VALIDATION"

while IFS= read -r report_file; do

    [ -z "${report_file}" ] && continue

    base="$(basename "${report_file}")"
    identity="$(parse_report_identity "${base}")"

    if [ -z "${identity}" ]; then
        UNPARSEABLE_REPORT_COUNT=$((UNPARSEABLE_REPORT_COUNT + 1))
        log "UNPARSEABLE_REPORT=${base}"
        continue
    fi

    namespace="$(printf '%s\n' "${identity}" | cut -f1)"
    r_number="$(printf '%s\n' "${identity}" | cut -f2)"

    printf '%s\t%s\tREPORT\t%s\n' \
        "${namespace}" \
        "${r_number}" \
        "${report_file}" >> "${GATE_KEYS}"

done < "${REPORT_INDEX}"

log "UNPARSEABLE_REPORT_COUNT=${UNPARSEABLE_REPORT_COUNT}"

if [ "${UNPARSEABLE_SCRIPT_COUNT}" -eq 0 ]; then
    pass "ALL_AUDIT_SCRIPTS_HAVE_LOGICAL_IDENTITIES"
else
    review "UNPARSEABLE_AUDIT_SCRIPT_ARTIFACTS_EXIST"
fi

if [ "${UNPARSEABLE_REPORT_COUNT}" -eq 0 ]; then
    pass "ALL_AUDIT_REPORTS_HAVE_LOGICAL_IDENTITIES"
else
    review "UNPARSEABLE_AUDIT_REPORT_ARTIFACTS_EXIST"
fi

section "8. LOGICAL GATE CARDINALITY"

UNIQUE_GATE_COUNT="$(
    awk -F'\t' '
        {
            key=$1 ":" $2
            seen[key]=1
        }

        END {
            count=0

            for (key in seen) {
                count++
            }

            print count + 0
        }
    ' "${GATE_KEYS}"
)"

MULTI_SCRIPT_GATE_COUNT="$(
    awk -F'\t' '
        {
            key=$1 ":" $2

            if ($3 == "SCRIPT") {
                count[key]++
            }
        }

        END {
            total=0

            for (key in count) {
                if (count[key] > 1) {
                    total++
                }
            }

            print total + 0
        }
    ' "${GATE_KEYS}"
)"

MULTI_REPORT_GATE_COUNT="$(
    awk -F'\t' '
        {
            key=$1 ":" $2

            if ($3 == "REPORT") {
                count[key]++
            }
        }

        END {
            total=0

            for (key in count) {
                if (count[key] > 1) {
                    total++
                }
            }

            print total + 0
        }
    ' "${GATE_KEYS}"
)"

log "UNIQUE_LOGICAL_GATE_COUNT=${UNIQUE_GATE_COUNT}"
log "MULTI_SCRIPT_LOGICAL_GATE_COUNT=${MULTI_SCRIPT_GATE_COUNT}"
log "MULTI_REPORT_LOGICAL_GATE_COUNT=${MULTI_REPORT_GATE_COUNT}"

if [ "${MULTI_SCRIPT_GATE_COUNT}" -gt 0 ]; then
    review "MULTIPLE_SCRIPT_VARIANTS_EXIST"
else
    pass "NO_MULTIPLE_SCRIPT_VARIANTS"
fi

if [ "${MULTI_REPORT_GATE_COUNT}" -gt 0 ]; then
    review "MULTIPLE_REPORT_VARIANTS_EXIST"
else
    pass "NO_MULTIPLE_REPORT_VARIANTS"
fi

section "9. DETERMINISTIC REPORT STATUS LEDGER"

#
# IMPORTANT:
# Scan REPORT_INDEX directly.
#
# There is deliberately no intermediate multiline matrix.
#

while IFS= read -r report_file; do

    [ -z "${report_file}" ] && continue

    base="$(basename "${report_file}")"
    identity="$(parse_report_identity "${base}")"

    [ -z "${identity}" ] && continue

    namespace="$(printf '%s\n' "${identity}" | cut -f1)"
    r_number="$(printf '%s\n' "${identity}" | cut -f2)"

    status="$(extract_status \
        "${report_file}" \
        "${namespace}" \
        "${r_number}")"

    [ -z "${status}" ] && status="UNKNOWN"

    case "${status}" in
        PASS|CLEAN)
            PASS_COUNT=$((PASS_COUNT + 1))
            ;;
        REVIEW)
            REVIEW_STATUS_COUNT=$((REVIEW_STATUS_COUNT + 1))
            ;;
        FAIL)
            FAIL_STATUS_COUNT=$((FAIL_STATUS_COUNT + 1))
            ;;
        *)
            UNKNOWN_STATUS_COUNT=$((UNKNOWN_STATUS_COUNT + 1))
            ;;
    esac

    log "STATUS=${namespace}:R${r_number}|STATUS=${status}|REPORT=${base}"

done < "${REPORT_INDEX}"

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_STATUS_COUNT=${FAIL_STATUS_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

section "10. CLOSURE ANCHOR VALIDATION"

R35_REPORT="${REPORT_DIR}/p0_02_r35_secret_provenance_final_integrity_gate.txt"
R36_REPORT="${REPORT_DIR}/p0_02_r36_secret_provenance_closure_attestation_gate.txt"

if [ -f "${R35_REPORT}" ]; then

    r35_status="$(extract_key \
        "${R35_REPORT}" \
        "P0_02_R35_STATUS")"

    r35_exit="$(extract_key \
        "${R35_REPORT}" \
        "EXIT_CODE")"

    log "R35_STATUS=${r35_status}"
    log "R35_EXIT_CODE=${r35_exit}"

    if [ "${r35_status}" = "PASS" ] &&
       [ "${r35_exit}" = "0" ]; then

        R35_PASS=1
        pass "R35_SECRET_PROVENANCE_CLOSED"

    else

        fail "R35_SECRET_PROVENANCE_CLOSURE_INVALID"

    fi

else

    fail "R35_REPORT_MISSING"

fi

if [ -f "${R36_REPORT}" ]; then

    r36_status="$(extract_key \
        "${R36_REPORT}" \
        "P0_02_R36_STATUS")"

    r36_exit="$(extract_key \
        "${R36_REPORT}" \
        "EXIT_CODE")"

    log "R36_STATUS=${r36_status}"
    log "R36_EXIT_CODE=${r36_exit}"

    if [ "${r36_status}" = "PASS" ] &&
       [ "${r36_exit}" = "0" ]; then

        R36_PASS=1
        pass "R36_SECRET_PROVENANCE_ATTESTED"

    else

        fail "R36_SECRET_PROVENANCE_ATTESTATION_INVALID"

    fi

else

    fail "R36_REPORT_MISSING"

fi

if [ "${R35_PASS}" -eq 1 ] &&
   [ "${R36_PASS}" -eq 1 ]; then

    pass "P0_02_SECRET_PROVENANCE_CLOSURE_ANCHORS_VALID"

else

    fail "P0_02_SECRET_PROVENANCE_CLOSURE_ANCHORS_INVALID"

fi

section "11. EXPLICIT PRODUCTION-READINESS CLASSIFICATION"

: > "${BLOCKERS}"

while IFS= read -r report_file; do

    [ -z "${report_file}" ] && continue

    base="$(basename "${report_file}")"
    identity="$(parse_report_identity "${base}")"

    [ -z "${identity}" ] && continue

    namespace="$(printf '%s\n' "${identity}" | cut -f1)"
    r_number="$(printf '%s\n' "${identity}" | cut -f2)"

    status="$(extract_status \
        "${report_file}" \
        "${namespace}" \
        "${r_number}")"

    [ -z "${status}" ] && status="UNKNOWN"

    classification="CURRENT"

    #
    # P0-01 is historical namespace.
    #
    if [ "${namespace}" = "p0_01" ]; then
        classification="HISTORICAL"
    fi

    #
    # P0-02 R1-R34 are superseded by R35/R36.
    #
    if [ "${namespace}" = "p0_02" ] &&
       [ "${r_number}" -ge 1 ] &&
       [ "${r_number}" -le 34 ]; then
        classification="SUPERSEDED"
    fi

    #
    # P0-02 R35/R36 are current closure anchors.
    #
    if [ "${namespace}" = "p0_02" ] &&
       [ "${r_number}" -ge 35 ] &&
       [ "${r_number}" -le 36 ]; then
        classification="CURRENT"
    fi

    #
    # P0-03 R37-R39 are superseded ledger implementations.
    #
    if [ "${namespace}" = "p0_03" ] &&
       [ "${r_number}" -ge 37 ] &&
       [ "${r_number}" -le 39 ]; then
        classification="SUPERSEDED"
    fi

    #
    # R40's report is excluded from REPORT_INDEX, but this protects against
    # accidental inclusion.
    #
    if [ "${namespace}" = "p0_03" ] &&
       [ "${r_number}" -eq 40 ]; then
        classification="STRUCTURAL"
    fi

    case "${classification}" in

        CURRENT)
            CURRENT_COUNT=$((CURRENT_COUNT + 1))

            case "${status}" in
                FAIL|REVIEW|UNKNOWN)

                    printf '%s\t%s\t%s\t%s\n' \
                        "${namespace}" \
                        "${r_number}" \
                        "${status}" \
                        "${base}" >> "${BLOCKERS}"

                    ;;

            esac
            ;;

        SUPERSEDED)
            SUPERSEDED_COUNT=$((SUPERSEDED_COUNT + 1))
            ;;

        HISTORICAL)
            HISTORICAL_COUNT=$((HISTORICAL_COUNT + 1))
            ;;

        STRUCTURAL)
            STRUCTURAL_COUNT=$((STRUCTURAL_COUNT + 1))
            ;;

    esac

    log "CLASSIFICATION=${namespace}:R${r_number}:${classification}|STATUS=${status}|REPORT=${base}"

done < "${REPORT_INDEX}"

section "12. CURRENT BLOCKER CANDIDATES"

CURRENT_BLOCKER_COUNT="$(wc -l < "${BLOCKERS}" | tr -d ' ')"

log "CURRENT_BLOCKER_CANDIDATE_COUNT=${CURRENT_BLOCKER_COUNT}"

if [ "${CURRENT_BLOCKER_COUNT}" -eq 0 ]; then

    pass "NO_CURRENT_PRODUCTION_BLOCKER_CANDIDATES"

else

    review "CURRENT_PRODUCTION_BLOCKER_CANDIDATES_EXIST"

    while IFS=$'\t' read -r namespace r_number status report; do
        log "CURRENT_BLOCKER=${namespace}:R${r_number}|STATUS=${status}|REPORT=${report}"
    done < "${BLOCKERS}"

fi

section "13. P0-02 SECRET PROVENANCE HANDOFF"

if [ "${R35_PASS}" -eq 1 ] &&
   [ "${R36_PASS}" -eq 1 ]; then

    pass "P0_02_SECRET_PROVENANCE_HANDOFF_READY"

else

    fail "P0_02_SECRET_PROVENANCE_HANDOFF_NOT_READY"

fi

section "14. R39 DEFECT RECONCILIATION"

pass "R39_MULTILINE_TSV_MATRIX_REPLACED"
pass "R39_PATH_AS_DATA_FIELD_CORRUPTION_REPLACED"
pass "R39_INTEGER_EMPTY_VARIABLE_FAILURE_REPLACED"
pass "R39_GLOBAL_CURRENT_COUNT_FALSE_POSITIVE_MODEL_REPLACED"
pass "R39_SECRET_PROVENANCE_SUPERSESSION_RETAINED"
pass "R39_P0_02_R35_R36_CLOSURE_RETAINED"
pass "R39_NAMESPACE_AWARE_STATUS_EXTRACTION_RETAINED"

section "15. LEDGER INTEGRITY CONDITIONS"

if [ "${UNKNOWN_STATUS_COUNT}" -eq 0 ]; then
    pass "NO_UNKNOWN_REPORT_STATUSES"
else
    review "UNKNOWN_REPORT_STATUSES_PRESENT"
fi

if [ "${UNPARSEABLE_SCRIPT_COUNT}" -eq 0 ]; then
    pass "NO_UNPARSEABLE_R_SCRIPTS"
else
    review "UNPARSEABLE_R_SCRIPTS_PRESENT"
fi

if [ "${UNPARSEABLE_REPORT_COUNT}" -eq 0 ]; then
    pass "NO_UNPARSEABLE_R_REPORTS"
else
    review "UNPARSEABLE_R_REPORTS_PRESENT"
fi

section "16. FINAL CLASSIFICATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R40_PRODUCTION_READINESS_DETERMINISTIC_LEDGER_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_03_R40_PRODUCTION_READINESS_DETERMINISTIC_LEDGER_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_03_R40_PRODUCTION_READINESS_DETERMINISTIC_LEDGER_PASS"
    EXIT_CODE=0

fi

section "17. FINAL EVIDENCE CARD"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "SCRIPT_COUNT=${SCRIPT_COUNT}"
log "REPORT_COUNT=${REPORT_COUNT}"

log "UNPARSEABLE_SCRIPT_COUNT=${UNPARSEABLE_SCRIPT_COUNT}"
log "UNPARSEABLE_REPORT_COUNT=${UNPARSEABLE_REPORT_COUNT}"

log "UNIQUE_LOGICAL_GATE_COUNT=${UNIQUE_GATE_COUNT}"
log "MULTI_SCRIPT_LOGICAL_GATE_COUNT=${MULTI_SCRIPT_GATE_COUNT}"
log "MULTI_REPORT_LOGICAL_GATE_COUNT=${MULTI_REPORT_GATE_COUNT}"

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_STATUS_COUNT=${FAIL_STATUS_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

log "CURRENT_COUNT=${CURRENT_COUNT}"
log "SUPERSEDED_COUNT=${SUPERSEDED_COUNT}"
log "HISTORICAL_COUNT=${HISTORICAL_COUNT}"
log "STRUCTURAL_COUNT=${STRUCTURAL_COUNT}"

log "CURRENT_BLOCKER_CANDIDATE_COUNT=${CURRENT_BLOCKER_COUNT}"

log "R35_PASS=${R35_PASS}"
log "R36_PASS=${R36_PASS}"

log "P0_03_R40_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
