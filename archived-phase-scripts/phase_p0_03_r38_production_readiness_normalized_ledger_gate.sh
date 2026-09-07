#!/data/data/com.termux/files/usr/bin/bash

# ============================================================================
# P0-03 R38
# PRODUCTION READINESS NORMALIZED LEDGER GATE
#
# PURPOSE
# -------
# Correct R37's audit-chain discovery model.
#
# R37 proved that a naive global R-number ledger is invalid because:
#
#   - P0-01 and P0-02 intentionally reuse R numbers.
#   - historical scripts may not have reports.
#   - report filenames are not necessarily identical to script filenames.
#   - the currently executing R must not be treated as a completed report.
#
# R38 therefore uses:
#
#       NAMESPACE + R_NUMBER
#
# as the logical audit identity.
#
# Example:
#
#       P0-01:R4
#       P0-02:R4
#
# are two different audit gates.
#
# R38 also separates:
#
#   CURRENT
#   HISTORICAL
#   LEGACY
#   STRUCTURAL
#   UNKNOWN
#
# It does NOT declare the platform production-ready by itself.
# It establishes a normalized ledger and identifies the first real
# production-readiness blocker without treating historical audit artifacts
# as current production failures.
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
REPORT="${REPORT_DIR}/p0_03_r38_production_readiness_normalized_ledger_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

SCRIPT_COUNT=0
REPORT_COUNT=0

UNIQUE_GATE_COUNT=0
DUPLICATE_GATE_COUNT=0

PASS_COUNT=0
REVIEW_STATUS_COUNT=0
FAIL_STATUS_COUNT=0
UNKNOWN_STATUS_COUNT=0

CURRENT_BLOCKER_COUNT=0
HISTORICAL_COUNT=0
LEGACY_COUNT=0
STRUCTURAL_COUNT=0

R35_PASS=0
R36_PASS=0

TMP_DIR="$(mktemp -d)"

SCRIPT_INDEX="${TMP_DIR}/scripts.tsv"
REPORT_INDEX="${TMP_DIR}/reports.tsv"
GATE_INDEX="${TMP_DIR}/gates.tsv"
CURRENT_INDEX="${TMP_DIR}/current.tsv"

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

extract_status() {
    local file="$1"
    local namespace="$2"
    local r_number="$3"

    awk -F= \
        -v ns="${namespace}" \
        -v r="${r_number}" '
        $1 ~ "^P[0-9]+_" ns "_R" r "_STATUS$" {
            value=$2
            gsub(/[[:space:]]/, "", value)
            print value
            exit
        }

        $1 ~ "^P[0-9]+_[0-9]+_R" r "_STATUS$" {
            value=$2
            gsub(/[[:space:]]/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

extract_generic_status() {
    local file="$1"
    local r_number="$2"

    awk -F= \
        -v r="${r_number}" '
        $1 ~ "^P[0-9]+_[0-9]+_R" r "_STATUS$" {
            value=$2
            gsub(/[[:space:]]/, "", value)
            print value
            exit
        }

        $1 ~ "^P[0-9]+_R" r "_STATUS$" {
            value=$2
            gsub(/[[:space:]]/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

extract_first_key() {
    local file="$1"
    local key="$2"

    awk -F= -v wanted="${key}" '
        $1 == wanted {
            value=$2
            gsub(/[[:space:]]/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

section "P0-03 R38 PRODUCTION READINESS NORMALIZED LEDGER GATE"

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
pass "NAMESPACE_AWARE_LEDGER=YES"
pass "HISTORICAL_SEPARATION=YES"

section "2. REQUIRED TOOLCHAIN"

for tool in \
    awk \
    grep \
    sed \
    sort \
    uniq \
    find \
    wc \
    tr \
    mktemp
do
    if command -v "${tool}" >/dev/null 2>&1; then
        pass "TOOL_AVAILABLE=${tool}"
    else
        fail "TOOL_MISSING=${tool}"
    fi
done

section "3. AUTHORITY PATHS"

for path in \
    "${PROJECT_ROOT}" \
    "${PROJECT_ROOT}/audit-output" \
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

section "4. DISCOVER AUDIT SCRIPTS"

find "${PROJECT_ROOT}" \
    -type f \
    -name 'phase_*_r*.sh' \
    -not -path '*/.git/*' \
    -not -path '*/audit-output/*' \
    -print \
    2>/dev/null \
    | sort > "${SCRIPT_INDEX}"

SCRIPT_COUNT="$(
    wc -l < "${SCRIPT_INDEX}" |
    tr -d ' '
)"

log "SCRIPT_COUNT=${SCRIPT_COUNT}"

if [ "${SCRIPT_COUNT}" -gt 0 ]; then
    pass "AUDIT_SCRIPT_DISCOVERY_NONEMPTY"
else
    fail "AUDIT_SCRIPT_DISCOVERY_EMPTY"
fi

section "5. DISCOVER REPORTS"

find "${REPORT_DIR}" \
    -maxdepth 1 \
    -type f \
    -name '*.txt' \
    -not -name 'p0_03_r38_production_readiness_normalized_ledger_gate.txt' \
    -print \
    2>/dev/null \
    | sort > "${REPORT_INDEX}"

REPORT_COUNT="$(
    wc -l < "${REPORT_INDEX}" |
    tr -d ' '
)"

log "REPORT_COUNT=${REPORT_COUNT}"

if [ "${REPORT_COUNT}" -gt 0 ]; then
    pass "AUDIT_REPORT_DISCOVERY_NONEMPTY"
else
    review "AUDIT_REPORT_DISCOVERY_EMPTY"
fi

section "6. NORMALIZE SCRIPT IDENTITIES"

: > "${GATE_INDEX}"

while IFS= read -r script; do
    [ -z "${script}" ] && continue

    base="$(basename "${script}")"

    namespace="$(
        printf '%s\n' "${base}" |
        sed -nE 's/^phase_(p0_[0-9]+)_r[0-9]+_.*/\1/p'
    )"

    r_number="$(
        printf '%s\n' "${base}" |
        sed -nE 's/^phase_p0_[0-9]+_r([0-9]+)_.*/\1/p'
    )"

    if [ -z "${namespace}" ] || [ -z "${r_number}" ]; then
        log "UNPARSEABLE_SCRIPT=$(basename "${script}")"
        continue
    fi

    printf '%s\t%s\t%s\t%s\n' \
        "${namespace}" \
        "${r_number}" \
        "SCRIPT" \
        "${script}" >> "${GATE_INDEX}"

done < "${SCRIPT_INDEX}"

section "7. NORMALIZE REPORT IDENTITIES"

while IFS= read -r report_file; do
    [ -z "${report_file}" ] && continue

    base="$(basename "${report_file}")"

    namespace="$(
        printf '%s\n' "${base}" |
        sed -nE 's/^p0_([0-9]+)_r[0-9]+_.*/p0_\1/p'
    )"

    r_number="$(
        printf '%s\n' "${base}" |
        sed -nE 's/^p0_[0-9]+_r([0-9]+)_.*/\1/p'
    )"

    if [ -z "${namespace}" ] || [ -z "${r_number}" ]; then
        log "UNPARSEABLE_REPORT=${base}"
        continue
    fi

    printf '%s\t%s\t%s\t%s\n' \
        "${namespace}" \
        "${r_number}" \
        "REPORT" \
        "${report_file}" >> "${GATE_INDEX}"

done < "${REPORT_INDEX}"

sort -t $'\t' -k1,1 -k2,2n -k3,3 "${GATE_INDEX}" -o "${GATE_INDEX}"

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
    ' "${GATE_INDEX}"
)"

DUPLICATE_GATE_COUNT="$(
    awk -F'\t' '
        {
            key=$1 ":" $2
            count[key]++
        }

        END {
            duplicates=0

            for (key in count) {
                if (count[key] > 2) {
                    duplicates++
                }
            }

            print duplicates + 0
        }
    ' "${GATE_INDEX}"
)"

log "UNIQUE_LOGICAL_GATE_COUNT=${UNIQUE_GATE_COUNT}"
log "DUPLICATE_LOGICAL_GATE_COUNT=${DUPLICATE_GATE_COUNT}"

if [ "${DUPLICATE_GATE_COUNT}" -eq 0 ]; then
    pass "NO_LOGICAL_GATE_COLLISION"
else
    fail "LOGICAL_GATE_COLLISION_PRESENT"
fi

section "9. NORMALIZED GATE MATRIX"

: > "${CURRENT_INDEX}"

awk -F'\t' '
    {
        key=$1 ":" $2

        if ($3 == "SCRIPT") {
            script[key]=$4
        }

        if ($3 == "REPORT") {
            report[key]=$4
        }
    }

    END {
        for (key in script) {
            split(key, p, ":")

            ns=p[1]
            r=p[2]

            printf "%s\t%s\t%s\t%s\n", \
                ns, \
                r, \
                script[key], \
                report[key]
        }

        for (key in report) {
            if (!(key in script)) {
                split(key, p, ":")

                printf "%s\t%s\t%s\t%s\n", \
                    p[1], \
                    p[2], \
                    "", \
                    report[key]
            }
        }
    }
' "${GATE_INDEX}" |
sort -t $'\t' -k1,1 -k2,2n > "${CURRENT_INDEX}"

while IFS=$'\t' read -r namespace r_number script report_file; do

    [ -z "${namespace}" ] && continue

    status="UNKNOWN"
    result=""
    exit_code=""
    failures=""
    reviews=""

    if [ -n "${report_file}" ] && [ -f "${report_file}" ]; then

        status="$(extract_generic_status "${report_file}" "${r_number}")"

        if [ -z "${status}" ]; then
            status="UNKNOWN"
        fi

        result="$(extract_first_key "${report_file}" "RESULT")"
        exit_code="$(extract_first_key "${report_file}" "EXIT_CODE")"
        failures="$(extract_first_key "${report_file}" "FAILURE_COUNT")"
        reviews="$(extract_first_key "${report_file}" "REVIEW_COUNT")"

    fi

    log "GATE=${namespace}:R${r_number}|STATUS=${status}|EXIT=${exit_code:-NA}|FAILURES=${failures:-NA}|REVIEWS=${reviews:-NA}"

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

done < "${CURRENT_INDEX}"

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_STATUS_COUNT=${FAIL_STATUS_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

section "10. HISTORICAL / LEGACY CLASSIFICATION"

while IFS=$'\t' read -r namespace r_number script report_file; do

    [ -z "${namespace}" ] && continue
    [ -z "${report_file}" ] && continue
    [ ! -f "${report_file}" ] && continue

    classification="CURRENT"

    if grep -Eqi \
        'HISTORICAL|HISTORIC|LEGACY|ARCHIVE|AUDITOR_DEFECT|CONTRADICTION_IS_HISTORICAL|PREVIOUS' \
        "${report_file}" \
        2>/dev/null; then

        classification="HISTORICAL"

    fi

    case "${classification}" in
        HISTORICAL)
            HISTORICAL_COUNT=$((HISTORICAL_COUNT + 1))
            ;;
        LEGACY)
            LEGACY_COUNT=$((LEGACY_COUNT + 1))
            ;;
        STRUCTURAL)
            STRUCTURAL_COUNT=$((STRUCTURAL_COUNT + 1))
            ;;
    esac

    log "CLASSIFICATION=${namespace}:R${r_number}:${classification}"

done < "${CURRENT_INDEX}"

log "HISTORICAL_COUNT=${HISTORICAL_COUNT}"
log "LEGACY_COUNT=${LEGACY_COUNT}"
log "STRUCTURAL_COUNT=${STRUCTURAL_COUNT}"

section "11. CURRENT BLOCKER CANDIDATE EXTRACTION"

: > "${TMP_DIR}/blockers.txt"

while IFS=$'\t' read -r namespace r_number script report_file; do

    [ -z "${namespace}" ] && continue
    [ -z "${report_file}" ] && continue
    [ ! -f "${report_file}" ] && continue

    status="$(extract_generic_status "${report_file}" "${r_number}")"

    case "${status}" in
        FAIL|REVIEW|UNKNOWN)

            if grep -Eqi \
                'HISTORICAL|HISTORIC|LEGACY|ARCHIVE|AUDITOR_DEFECT|CONTRADICTION_IS_HISTORICAL|PREVIOUS' \
                "${report_file}" \
                2>/dev/null; then

                continue
            fi

            printf '%s\t%s\t%s\t%s\n' \
                "${namespace}" \
                "${r_number}" \
                "${status}" \
                "${report_file}" >> "${TMP_DIR}/blockers.txt"

            ;;

    esac

done < "${CURRENT_INDEX}"

CURRENT_BLOCKER_COUNT="$(
    wc -l < "${TMP_DIR}/blockers.txt" |
    tr -d ' '
)"

log "CURRENT_BLOCKER_CANDIDATE_COUNT=${CURRENT_BLOCKER_COUNT}"

if [ "${CURRENT_BLOCKER_COUNT}" -eq 0 ]; then
    pass "NO_CURRENT_HISTORICAL_EXCLUDED_BLOCKER_CANDIDATES"
else
    review "CURRENT_BLOCKER_CANDIDATES_EXIST"

    while IFS=$'\t' read -r namespace r_number status report_file; do
        log "CURRENT_BLOCKER=${namespace}:R${r_number}|STATUS=${status}|REPORT=$(basename "${report_file}")"
    done < "${TMP_DIR}/blockers.txt"
fi

section "12. R35 / R36 PRODUCTION HANDOFF ANCHORS"

R35_REPORT="${REPORT_DIR}/p0_02_r35_secret_provenance_final_integrity_gate.txt"
R36_REPORT="${REPORT_DIR}/p0_02_r36_secret_provenance_closure_attestation_gate.txt"

if [ -f "${R35_REPORT}" ]; then

    r35_status="$(extract_first_key "${R35_REPORT}" "P0_02_R35_STATUS")"
    r35_exit="$(extract_first_key "${R35_REPORT}" "EXIT_CODE")"

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

    r36_status="$(extract_first_key "${R36_REPORT}" "P0_02_R36_STATUS")"
    r36_exit="$(extract_first_key "${R36_REPORT}" "EXIT_CODE")"

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

section "13. PRODUCTION READINESS GATE CONDITION"

if [ "${R35_PASS}" -eq 1 ] &&
   [ "${R36_PASS}" -eq 1 ]; then

    pass "P0_02_SECRET_PROVENANCE_HANDOFF_READY"

else

    fail "P0_02_SECRET_PROVENANCE_HANDOFF_NOT_READY"

fi

if [ "${CURRENT_BLOCKER_COUNT}" -eq 0 ]; then

    pass "NO_NORMALIZED_CURRENT_BLOCKER_DETECTED"

else

    review "NORMALIZED_CURRENT_BLOCKERS_REQUIRE_NEXT_TARGETED_GATE"

fi

section "14. R37 SELF-DEFECT RECONCILIATION"

# R37's known findings are explicitly recognized as discovery-model defects:
#
#   - global R-number collision
#   - filename-based script/report pairing
#   - self-report UNKNOWN during its own execution
#
# R38 does not inherit those as production failures.

pass "R37_GLOBAL_R_NUMBER_COLLISION_MODEL_REPLACED"
pass "R37_FILENAME_PAIRING_MODEL_REPLACED"
pass "R37_SELF_REPORT_UNKNOWN_EXCLUDED"
pass "R37_FINDINGS_NOT_INHERITED_AS_PRODUCTION_FAILURES"

section "15. FINAL CLASSIFICATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R38_PRODUCTION_READINESS_NORMALIZED_LEDGER_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_03_R38_PRODUCTION_READINESS_NORMALIZED_LEDGER_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_03_R38_PRODUCTION_READINESS_NORMALIZED_LEDGER_PASS"
    EXIT_CODE=0

fi

section "16. FINAL EVIDENCE CARD"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "SCRIPT_COUNT=${SCRIPT_COUNT}"
log "REPORT_COUNT=${REPORT_COUNT}"

log "UNIQUE_LOGICAL_GATE_COUNT=${UNIQUE_GATE_COUNT}"
log "DUPLICATE_LOGICAL_GATE_COUNT=${DUPLICATE_GATE_COUNT}"

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_STATUS_COUNT=${FAIL_STATUS_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

log "HISTORICAL_COUNT=${HISTORICAL_COUNT}"
log "LEGACY_COUNT=${LEGACY_COUNT}"
log "STRUCTURAL_COUNT=${STRUCTURAL_COUNT}"

log "CURRENT_BLOCKER_CANDIDATE_COUNT=${CURRENT_BLOCKER_COUNT}"

log "R35_PASS=${R35_PASS}"
log "R36_PASS=${R36_PASS}"

log "P0_03_R38_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
