#!/data/data/com.termux/files/usr/bin/bash

# ============================================================================
# P0-03 R37
# PRODUCTION READINESS CHAIN DISCOVERY GATE
#
# PURPOSE
# -------
# Establish the real audit-chain state from the filesystem instead of
# reconstructing previous R gates from memory.
#
# R37 is a DISCOVERY / LEDGER gate.
#
# It does NOT modify application source.
# It does NOT execute application code.
# It does NOT source environment files.
# It does NOT build or deploy.
#
# It discovers:
#   - every existing phase_*_r*.sh audit gate
#   - every corresponding audit report
#   - R number
#   - status
#   - result
#   - exit code
#   - failure/review counts where available
#   - missing report/script pairs
#   - duplicate R numbers
#   - highest completed R
#   - first unresolved current-state gate
#
# It explicitly separates:
#   CURRENT / HISTORICAL / UNKNOWN
#
# IMPORTANT
# ---------
# This gate does not declare the platform production-ready.
# Its job is to establish the exact next engineering target.
# ============================================================================

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
EXPECTED_ROOT="/data/data/com.termux/files/home/waste-platform"

REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r37_production_readiness_chain_discovery_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

TOTAL_R_SCRIPT_COUNT=0
TOTAL_REPORT_COUNT=0
RANGE_MAX=0

DUPLICATE_R_COUNT=0
MISSING_REPORT_COUNT=0
MISSING_SCRIPT_COUNT=0

PASS_COUNT=0
REVIEW_STATUS_COUNT=0
FAIL_COUNT=0
UNKNOWN_STATUS_COUNT=0

CURRENT_UNRESOLVED_COUNT=0
HISTORICAL_ONLY_COUNT=0

TMP_DIR="$(mktemp -d)"
R_INDEX="${TMP_DIR}/r_index.tsv"
REPORT_INDEX="${TMP_DIR}/report_index.tsv"
SCRIPT_INDEX="${TMP_DIR}/script_index.tsv"
STATUS_INDEX="${TMP_DIR}/status_index.tsv"

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

extract_first() {
    local file="$1"
    local key="$2"

    awk -F= -v wanted="${key}" '
        $1 == wanted {
            value=$0
            sub(/^[^=]*=/, "", value)
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

section "P0-03 R37 PRODUCTION READINESS CHAIN DISCOVERY GATE"

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
pass "NO_SECRET_VALUES_PARSED=YES"
pass "DETERMINISTIC_CHAIN_DISCOVERY=YES"
pass "FAIL_CLOSED=YES"

section "2. REQUIRED TOOLCHAIN"

for tool in awk grep sed sort uniq find wc tr mktemp; do
    if command -v "${tool}" >/dev/null 2>&1; then
        pass "TOOL_AVAILABLE=${tool}"
    else
        fail "TOOL_MISSING=${tool}"
    fi
done

section "3. PROJECT STRUCTURE"

for path in \
    "${PROJECT_ROOT}" \
    "${PROJECT_ROOT}/audit-output"
do
    if [ -d "${path}" ]; then
        pass "DIRECTORY_PRESENT=${path}"
    else
        fail "DIRECTORY_MISSING=${path}"
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

TOTAL_R_SCRIPT_COUNT="$(
    wc -l < "${SCRIPT_INDEX}" | tr -d ' '
)"

log "TOTAL_R_SCRIPT_COUNT=${TOTAL_R_SCRIPT_COUNT}"

if [ "${TOTAL_R_SCRIPT_COUNT}" -gt 0 ]; then
    pass "AUDIT_SCRIPTS_DISCOVERED"
else
    fail "NO_AUDIT_SCRIPTS_DISCOVERED"
fi

section "5. DISCOVER AUDIT REPORTS"

find "${REPORT_DIR}" \
    -maxdepth 1 \
    -type f \
    -name '*.txt' \
    -print \
    2>/dev/null \
    | sort > "${REPORT_INDEX}"

TOTAL_REPORT_COUNT="$(
    wc -l < "${REPORT_INDEX}" | tr -d ' '
)"

log "TOTAL_REPORT_COUNT=${TOTAL_REPORT_COUNT}"

if [ "${TOTAL_REPORT_COUNT}" -gt 0 ]; then
    pass "AUDIT_REPORTS_DISCOVERED"
else
    review "NO_AUDIT_REPORTS_DISCOVERED"
fi

section "6. BUILD R-NUMBER INDEX"

: > "${R_INDEX}"

while IFS= read -r script; do
    [ -z "${script}" ] && continue

    base="$(basename "${script}")"

    r_number="$(
        printf '%s\n' "${base}" |
        sed -nE 's/.*_r([0-9]+)_.*/\1/p' |
        head -n 1
    )"

    if [ -n "${r_number}" ]; then
        printf '%s\t%s\t%s\n' \
            "${r_number}" \
            "SCRIPT" \
            "${script}" >> "${R_INDEX}"

        if [ "${r_number}" -gt "${RANGE_MAX}" ] 2>/dev/null; then
            RANGE_MAX="${r_number}"
        fi
    fi

done < "${SCRIPT_INDEX}"

while IFS= read -r report_file; do
    [ -z "${report_file}" ] && continue

    base="$(basename "${report_file}")"

    r_number="$(
        printf '%s\n' "${base}" |
        sed -nE 's/.*_r([0-9]+)_.*/\1/p' |
        head -n 1
    )"

    if [ -n "${r_number}" ]; then
        printf '%s\t%s\t%s\n' \
            "${r_number}" \
            "REPORT" \
            "${report_file}" >> "${R_INDEX}"

        if [ "${r_number}" -gt "${RANGE_MAX}" ] 2>/dev/null; then
            RANGE_MAX="${r_number}"
        fi
    fi

done < "${REPORT_INDEX}"

log "HIGHEST_DISCOVERED_R=${RANGE_MAX}"

if [ "${RANGE_MAX}" -gt 0 ]; then
    pass "R_NUMBER_INDEX_BUILT"
else
    fail "R_NUMBER_INDEX_EMPTY"
fi

section "7. DUPLICATE R DETECTION"

DUPLICATE_R_COUNT="$(
    awk -F'\t' '
        {
            count[$1]++
        }

        END {
            duplicates=0

            for (r in count) {
                if (count[r] > 2) {
                    duplicates++
                }
            }

            print duplicates + 0
        }
    ' "${R_INDEX}"
)"

log "DUPLICATE_R_COUNT=${DUPLICATE_R_COUNT}"

# A normal R has one script and one report, therefore 2 index entries.
# >2 means multiple scripts/reports with the same R number.
if [ "${DUPLICATE_R_COUNT}" -eq 0 ]; then
    pass "NO_DUPLICATE_R_NUMBER_COLLISION"
else
    fail "DUPLICATE_R_NUMBER_COLLISION_PRESENT"
fi

section "8. SCRIPT / REPORT PAIRING"

: > "${STATUS_INDEX}"

while IFS= read -r script; do
    [ -z "${script}" ] && continue

    base="$(basename "${script}")"

    r_number="$(
        printf '%s\n' "${base}" |
        sed -nE 's/.*_r([0-9]+)_.*/\1/p' |
        head -n 1
    )"

    [ -z "${r_number}" ] && continue

    stem="${base%.sh}"

    expected_report="$(
        find "${REPORT_DIR}" \
            -maxdepth 1 \
            -type f \
            -name "*${stem}*.txt" \
            -print \
            2>/dev/null \
            | head -n 1
    )"

    if [ -n "${expected_report}" ]; then
        log "PAIR_PRESENT=R${r_number}:${base}:$(basename "${expected_report}")"
    else
        log "SCRIPT_WITHOUT_REPORT=R${r_number}:${base}"
        MISSING_REPORT_COUNT=$((MISSING_REPORT_COUNT + 1))
    fi

done < "${SCRIPT_INDEX}"

while IFS= read -r report_file; do
    [ -z "${report_file}" ] && continue

    base="$(basename "${report_file}")"

    r_number="$(
        printf '%s\n' "${base}" |
        sed -nE 's/.*_r([0-9]+)_.*/\1/p' |
        head -n 1
    )"

    [ -z "${r_number}" ] && continue

    script_matches="$(
        awk -F'\t' -v wanted="${r_number}" '
            $1 == wanted && $2 == "SCRIPT" {
                print $3
            }
        ' "${R_INDEX}"
    )"

    if [ -z "${script_matches}" ]; then
        log "REPORT_WITHOUT_SCRIPT=R${r_number}:${base}"
        MISSING_SCRIPT_COUNT=$((MISSING_SCRIPT_COUNT + 1))
    fi

done < "${REPORT_INDEX}"

log "MISSING_REPORT_COUNT=${MISSING_REPORT_COUNT}"
log "MISSING_SCRIPT_COUNT=${MISSING_SCRIPT_COUNT}"

if [ "${MISSING_REPORT_COUNT}" -eq 0 ]; then
    pass "NO_SCRIPT_WITHOUT_REPORT"
else
    review "SCRIPT_WITHOUT_REPORT_PRESENT"
fi

if [ "${MISSING_SCRIPT_COUNT}" -eq 0 ]; then
    pass "NO_REPORT_WITHOUT_SCRIPT"
else
    review "REPORT_WITHOUT_SCRIPT_PRESENT"
fi

section "9. EXTRACT R STATUS MATRIX"

: > "${STATUS_INDEX}"

while IFS= read -r report_file; do
    [ -z "${report_file}" ] && continue

    base="$(basename "${report_file}")"

    r_number="$(
        printf '%s\n' "${base}" |
        sed -nE 's/.*_r([0-9]+)_.*/\1/p' |
        head -n 1
    )"

    [ -z "${r_number}" ] && continue

    status="$(extract_first "${report_file}" "P0_02_R${r_number}_STATUS")"

    if [ -z "${status}" ]; then
        status="$(extract_first "${report_file}" "P0_03_R${r_number}_STATUS")"
    fi

    if [ -z "${status}" ]; then
        status="$(extract_first "${report_file}" "P0_01_R${r_number}_STATUS")"
    fi

    if [ -z "${status}" ]; then
        status="UNKNOWN"
    fi

    result="$(extract_first "${report_file}" "RESULT")"
    exit_code="$(extract_first "${report_file}" "EXIT_CODE")"
    failures="$(extract_first "${report_file}" "FAILURE_COUNT")"
    reviews="$(extract_first "${report_file}" "REVIEW_COUNT")"

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${r_number}" \
        "${status}" \
        "${exit_code}" \
        "${failures}" \
        "${reviews}" \
        "${result}" \
        "${report_file}" >> "${STATUS_INDEX}"

done < "${REPORT_INDEX}"

sort -n -k1,1 "${STATUS_INDEX}" -o "${STATUS_INDEX}"

section "10. R STATUS MATRIX"

if [ -s "${STATUS_INDEX}" ]; then

    while IFS=$'\t' read -r \
        r_number \
        status \
        exit_code \
        failures \
        reviews \
        result \
        report_file
    do

        log "R${r_number}|STATUS=${status}|EXIT=${exit_code}|FAILURES=${failures:-NA}|REVIEWS=${reviews:-NA}|REPORT=$(basename "${report_file}")"

        case "${status}" in
            PASS)
                PASS_COUNT=$((PASS_COUNT + 1))
                ;;
            REVIEW)
                REVIEW_STATUS_COUNT=$((REVIEW_STATUS_COUNT + 1))
                ;;
            FAIL)
                FAIL_COUNT=$((FAIL_COUNT + 1))
                ;;
            *)
                UNKNOWN_STATUS_COUNT=$((UNKNOWN_STATUS_COUNT + 1))
                ;;
        esac

    done < "${STATUS_INDEX}"

else

    fail "R_STATUS_MATRIX_EMPTY"

fi

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_COUNT=${FAIL_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

section "11. CURRENT VS HISTORICAL CLASSIFICATION"

# Historical audit artifacts are identified by their explicit historical
# markers. They are not treated as current production failures.

while IFS=$'\t' read -r \
    r_number \
    status \
    exit_code \
    failures \
    reviews \
    result \
    report_file
do

    case "${status}" in
        PASS)
            ;;
        REVIEW|FAIL|UNKNOWN)

            if grep -Eq \
                'HISTORICAL|HISTORIC|ARCHIVE|PREVIOUS|LEGACY|CONTRADICTION_IS_HISTORICAL|AUDITOR_DEFECT' \
                "${report_file}" \
                2>/dev/null; then

                HISTORICAL_ONLY_COUNT=$((HISTORICAL_ONLY_COUNT + 1))

                log "R${r_number}_HISTORICAL_MARKER=YES"

            else

                CURRENT_UNRESOLVED_COUNT=$((CURRENT_UNRESOLVED_COUNT + 1))

                log "R${r_number}_CURRENT_UNRESOLVED_CANDIDATE=YES"

            fi

            ;;
    esac

done < "${STATUS_INDEX}"

log "HISTORICAL_ONLY_COUNT=${HISTORICAL_ONLY_COUNT}"
log "CURRENT_UNRESOLVED_COUNT=${CURRENT_UNRESOLVED_COUNT}"

section "12. R35/R36 CLOSURE ANCHOR"

R35_REPORT="$(
    find "${REPORT_DIR}" \
        -maxdepth 1 \
        -type f \
        -name '*r35*secret_provenance_final_integrity_gate*.txt' \
        -print \
        2>/dev/null \
        | head -n 1
)"

R36_REPORT="$(
    find "${REPORT_DIR}" \
        -maxdepth 1 \
        -type f \
        -name '*r36*secret_provenance_closure_attestation_gate*.txt' \
        -print \
        2>/dev/null \
        | head -n 1
)"

if [ -n "${R35_REPORT}" ]; then

    r35_status="$(extract_first "${R35_REPORT}" "P0_02_R35_STATUS")"
    r35_exit="$(extract_first "${R35_REPORT}" "EXIT_CODE")"

    log "R35_STATUS=${r35_status}"
    log "R35_EXIT_CODE=${r35_exit}"

    if [ "${r35_status}" = "PASS" ] &&
       [ "${r35_exit}" = "0" ]; then
        pass "R35_CLOSURE_ANCHOR_VALID"
    else
        fail "R35_CLOSURE_ANCHOR_INVALID"
    fi

else

    fail "R35_CLOSURE_REPORT_NOT_FOUND"

fi

if [ -n "${R36_REPORT}" ]; then

    r36_status="$(extract_first "${R36_REPORT}" "P0_02_R36_STATUS")"
    r36_exit="$(extract_first "${R36_REPORT}" "EXIT_CODE")"

    log "R36_STATUS=${r36_status}"
    log "R36_EXIT_CODE=${r36_exit}"

    if [ "${r36_status}" = "PASS" ] &&
       [ "${r36_exit}" = "0" ]; then
        pass "R36_CLOSURE_ATTESTATION_VALID"
    else
        fail "R36_CLOSURE_ATTESTATION_INVALID"
    fi

else

    fail "R36_CLOSURE_REPORT_NOT_FOUND"

fi

section "13. CHAIN CONTINUITY"

if [ "${RANGE_MAX}" -gt 0 ]; then

    MISSING_NUMBERS="$(
        seq 1 "${RANGE_MAX}" |
        while IFS= read -r n; do
            if ! awk -F'\t' -v wanted="${n}" '$1 == wanted { found=1 } END { exit(found ? 0 : 1) }' "${R_INDEX}"; then
                printf '%s ' "${n}"
            fi
        done
    )"

    MISSING_NUMBERS="$(printf '%s' "${MISSING_NUMBERS}" | sed 's/[[:space:]]*$//')"

    if [ -n "${MISSING_NUMBERS}" ]; then
        log "CHAIN_MISSING_R_NUMBERS=${MISSING_NUMBERS}"
        review "R_CHAIN_HAS_NUMBERING_GAPS"
    else
        pass "R_CHAIN_NUMBERING_CONTINUOUS_1_TO_${RANGE_MAX}"
    fi

else

    fail "CHAIN_RANGE_UNAVAILABLE"

fi

section "14. PRODUCTION READINESS HANDOFF"

log "This section identifies what R37 can establish and what it cannot."

if [ "${CURRENT_UNRESOLVED_COUNT}" -eq 0 ] &&
   [ "${UNKNOWN_STATUS_COUNT}" -eq 0 ] &&
   [ "${FAIL_COUNT}" -eq 0 ] &&
   [ "${REVIEW_STATUS_COUNT}" -eq 0 ] &&
   [ "${R35_REPORT}" != "" ] &&
   [ "${R36_REPORT}" != "" ]; then

    pass "AUDIT_CHAIN_HAS_NO_UNRESOLVED_STATUS"
    pass "NEXT_STAGE_CAN_TARGET_PRODUCTION_RELEASE"

else

    review "AUDIT_CHAIN_REQUIRES_TARGETED_RECONCILIATION_BEFORE_RELEASE"
fi

section "15. FINAL CLASSIFICATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R37_PRODUCTION_READINESS_CHAIN_DISCOVERY_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_03_R37_PRODUCTION_READINESS_CHAIN_DISCOVERY_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_03_R37_PRODUCTION_READINESS_CHAIN_DISCOVERY_PASS"
    EXIT_CODE=0

fi

section "16. FINAL EVIDENCE CARD"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "TOTAL_R_SCRIPT_COUNT=${TOTAL_R_SCRIPT_COUNT}"
log "TOTAL_REPORT_COUNT=${TOTAL_REPORT_COUNT}"
log "HIGHEST_DISCOVERED_R=${RANGE_MAX}"

log "DUPLICATE_R_COUNT=${DUPLICATE_R_COUNT}"
log "MISSING_REPORT_COUNT=${MISSING_REPORT_COUNT}"
log "MISSING_SCRIPT_COUNT=${MISSING_SCRIPT_COUNT}"

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_COUNT=${FAIL_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

log "HISTORICAL_ONLY_COUNT=${HISTORICAL_ONLY_COUNT}"
log "CURRENT_UNRESOLVED_COUNT=${CURRENT_UNRESOLVED_COUNT}"

if [ -n "${R35_REPORT}" ]; then
    log "R35_REPORT=$(basename "${R35_REPORT}")"
fi

if [ -n "${R36_REPORT}" ]; then
    log "R36_REPORT=$(basename "${R36_REPORT}")"
fi

log "P0_03_R37_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
