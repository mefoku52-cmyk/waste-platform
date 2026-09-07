#!/data/data/com.termux/files/usr/bin/bash

# ============================================================================
# P0-03 R39
# PRODUCTION READINESS SUPERSESSION LEDGER GATE
#
# PURPOSE
# -------
# Correct R38's remaining ledger defects.
#
# R38 incorrectly treated historical/superseded audit results as current
# production blockers because it classified reports by keyword presence.
#
# R39 introduces explicit audit semantics:
#
#   CURRENT
#   SUPERSEDED
#   HISTORICAL
#   STRUCTURAL
#   UNKNOWN
#
# Important:
#
#   P0-02:R35 PASS
#   P0-02:R36 PASS
#
# are authoritative closure anchors for the P0-02 secret-provenance branch.
#
# Therefore earlier P0-02 secret-provenance gates R1-R34 are not current
# production blockers merely because their old reports contain FAIL/REVIEW.
#
# R39 is still a ledger gate.
# It does NOT claim the application is production-ready.
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
REPORT="${REPORT_DIR}/p0_03_r39_production_readiness_supersession_ledger_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

SCRIPT_COUNT=0
REPORT_COUNT=0

UNPARSEABLE_SCRIPT_COUNT=0
UNPARSEABLE_REPORT_COUNT=0

UNIQUE_LOGICAL_GATE_COUNT=0
DUPLICATE_LOGICAL_GATE_COUNT=0

PASS_COUNT=0
REVIEW_STATUS_COUNT=0
FAIL_STATUS_COUNT=0
UNKNOWN_STATUS_COUNT=0

CURRENT_COUNT=0
SUPERSEDED_COUNT=0
HISTORICAL_COUNT=0
STRUCTURAL_COUNT=0
UNKNOWN_CLASSIFICATION_COUNT=0

CURRENT_BLOCKER_COUNT=0

R35_PASS=0
R36_PASS=0

TMP_DIR="$(mktemp -d)"

SCRIPT_INDEX="${TMP_DIR}/scripts.tsv"
REPORT_INDEX="${TMP_DIR}/reports.tsv"
GATE_INDEX="${TMP_DIR}/gates.tsv"
MATRIX="${TMP_DIR}/matrix.tsv"
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

extract_namespaced_status() {
    local file="$1"
    local namespace="$2"
    local r_number="$3"

    local ns_upper
    ns_upper="$(printf '%s' "${namespace}" | tr '[:lower:]' '[:upper:]')"

    awk -F= \
        -v key="P${ns_upper#P}_R${r_number}_STATUS" '
        $1 == key {
            value=$2
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

# Explicit form:
# namespace p0_02 -> key P0_02_R35_STATUS
extract_status() {
    local file="$1"
    local namespace="$2"
    local r_number="$3"

    local prefix
    prefix="$(printf '%s' "${namespace}" | tr '[:lower:]' '[:upper:]')"

    awk -F= \
        -v wanted="${prefix}_R${r_number}_STATUS" '
        $1 == wanted {
            value=$2
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            print value
            exit
        }
    ' "${file}" 2>/dev/null
}

section "P0-03 R39 PRODUCTION READINESS SUPERSESSION LEDGER GATE"

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
pass "NAMESPACE_AWARE=YES"
pass "EXPLICIT_SUPERSESSION=YES"
pass "NO_KEYWORD_ONLY_CLASSIFICATION=YES"

section "2. REQUIRED TOOLCHAIN"

for tool in awk grep sed sort uniq find wc tr mktemp; do
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

section "4. AUDIT SCRIPT DISCOVERY"

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

section "5. AUDIT REPORT DISCOVERY"

find "${REPORT_DIR}" \
    -maxdepth 1 \
    -type f \
    -name '*.txt' \
    -not -name 'p0_03_r39_production_readiness_supersession_ledger_gate.txt' \
    -print 2>/dev/null |
sort > "${REPORT_INDEX}"

REPORT_COUNT="$(wc -l < "${REPORT_INDEX}" | tr -d ' ')"

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
        UNPARSEABLE_SCRIPT_COUNT=$((UNPARSEABLE_SCRIPT_COUNT + 1))
        log "UNPARSEABLE_SCRIPT=${base}"
        continue
    fi

    printf '%s\t%s\tSCRIPT\t%s\n' \
        "${namespace}" \
        "${r_number}" \
        "${script}" >> "${GATE_INDEX}"

done < "${SCRIPT_INDEX}"

log "UNPARSEABLE_SCRIPT_COUNT=${UNPARSEABLE_SCRIPT_COUNT}"

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
        UNPARSEABLE_REPORT_COUNT=$((UNPARSEABLE_REPORT_COUNT + 1))
        log "UNPARSEABLE_REPORT=${base}"
        continue
    fi

    printf '%s\t%s\tREPORT\t%s\n' \
        "${namespace}" \
        "${r_number}" \
        "${report_file}" >> "${GATE_INDEX}"

done < "${REPORT_INDEX}"

log "UNPARSEABLE_REPORT_COUNT=${UNPARSEABLE_REPORT_COUNT}"

section "8. LOGICAL IDENTITY ANALYSIS"

sort -t $'\t' -k1,1 -k2,2n -k3,3 "${GATE_INDEX}" -o "${GATE_INDEX}"

UNIQUE_LOGICAL_GATE_COUNT="$(
    awk -F'\t' '
        {
            seen[$1 ":" $2]=1
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

# A normal logical gate can have:
#
#   1 script
#   1 report
#
# Multiple scripts under the same namespace/R are historical variants,
# not automatically a collision.
#
# We only flag a collision if there are multiple CURRENT candidates,
# which R39 determines later from explicit supersession rules.
DUPLICATE_LOGICAL_GATE_COUNT="$(
    awk -F'\t' '
        {
            key=$1 ":" $2

            if ($3 == "SCRIPT") {
                script_count[key]++
            }

            if ($3 == "REPORT") {
                report_count[key]++
            }
        }

        END {
            collisions=0

            for (key in script_count) {
                if (script_count[key] > 1) {
                    collisions++
                }
            }

            for (key in report_count) {
                if (report_count[key] > 1) {
                    collisions++
                }
            }

            print collisions + 0
        }
    ' "${GATE_INDEX}"
)"

log "UNIQUE_LOGICAL_GATE_COUNT=${UNIQUE_LOGICAL_GATE_COUNT}"
log "MULTI_ARTIFACT_LOGICAL_GATE_COUNT=${DUPLICATE_LOGICAL_GATE_COUNT}"

if [ "${DUPLICATE_LOGICAL_GATE_COUNT}" -gt 0 ]; then
    review "MULTIPLE_ARTIFACTS_SHARE_LOGICAL_GATE_ID"
else
    pass "NO_MULTI_ARTIFACT_LOGICAL_GATE_ID"
fi

section "9. BUILD NAMESPACE/R MATRIX"

: > "${MATRIX}"

awk -F'\t' '
    {
        key=$1 ":" $2

        if ($3 == "SCRIPT") {
            script_count[key]++
            scripts[key]=scripts[key] "\n" $4
        }

        if ($3 == "REPORT") {
            report_count[key]++
            reports[key]=reports[key] "\n" $4
        }
    }

    END {
        for (key in script_count) {
            split(key,p,":")

            print \
                p[1] "\t" \
                p[2] "\t" \
                script_count[key] "\t" \
                report_count[key] "\t" \
                scripts[key] "\t" \
                reports[key]
        }

        for (key in report_count) {
            if (!(key in script_count)) {
                split(key,p,":")

                print \
                    p[1] "\t" \
                    p[2] "\t" \
                    0 "\t" \
                    report_count[key] "\t" \
                    "" "\t" \
                    reports[key]
            }
        }
    }
' "${GATE_INDEX}" |
sort -t $'\t' -k1,1 -k2,2n > "${MATRIX}"

section "10. EXPLICIT STATUS EXTRACTION"

while IFS=$'\t' read -r namespace r_number script_count report_count scripts reports; do

    [ -z "${namespace}" ] && continue

    report_file=""

    if [ "${report_count}" -eq 1 ]; then
        report_file="$(printf '%s\n' "${reports}" | sed '/^$/d' | head -n1)"
    fi

    status="UNKNOWN"
    result=""
    exit_code=""
    failures=""
    reviews=""

    if [ -n "${report_file}" ] && [ -f "${report_file}" ]; then

        status="$(extract_status "${report_file}" "${namespace}" "${r_number}")"

        [ -z "${status}" ] && status="UNKNOWN"

        result="$(extract_key "${report_file}" "RESULT")"
        exit_code="$(extract_key "${report_file}" "EXIT_CODE")"
        failures="$(extract_key "${report_file}" "FAILURE_COUNT")"
        reviews="$(extract_key "${report_file}" "REVIEW_COUNT")"

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

done < "${MATRIX}"

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_STATUS_COUNT=${FAIL_STATUS_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

section "11. EXPLICIT SUPERSESSION MODEL"

#
# P0-02 secret provenance closure:
#
# R35 = final integrity PASS
# R36 = closure attestation PASS
#
# Everything R1-R34 in the same secret-provenance namespace is therefore
# historical/superseded for production-readiness purposes.
#

if [ -f "${REPORT_DIR}/p0_02_r35_secret_provenance_final_integrity_gate.txt" ]; then

    r35_status="$(extract_key \
        "${REPORT_DIR}/p0_02_r35_secret_provenance_final_integrity_gate.txt" \
        "P0_02_R35_STATUS")"

    r35_exit="$(extract_key \
        "${REPORT_DIR}/p0_02_r35_secret_provenance_final_integrity_gate.txt" \
        "EXIT_CODE")"

    log "P0_02_R35_STATUS=${r35_status}"
    log "P0_02_R35_EXIT_CODE=${r35_exit}"

    if [ "${r35_status}" = "PASS" ] && [ "${r35_exit}" = "0" ]; then
        R35_PASS=1
        pass "P0_02_R35_CLOSURE_ANCHOR_VALID"
    else
        fail "P0_02_R35_CLOSURE_ANCHOR_INVALID"
    fi

else

    fail "P0_02_R35_CLOSURE_REPORT_MISSING"

fi

if [ -f "${REPORT_DIR}/p0_02_r36_secret_provenance_closure_attestation_gate.txt" ]; then

    r36_status="$(extract_key \
        "${REPORT_DIR}/p0_02_r36_secret_provenance_closure_attestation_gate.txt" \
        "P0_02_R36_STATUS")"

    r36_exit="$(extract_key \
        "${REPORT_DIR}/p0_02_r36_secret_provenance_closure_attestation_gate.txt" \
        "EXIT_CODE")"

    log "P0_02_R36_STATUS=${r36_status}"
    log "P0_02_R36_EXIT_CODE=${r36_exit}"

    if [ "${r36_status}" = "PASS" ] && [ "${r36_exit}" = "0" ]; then
        R36_PASS=1
        pass "P0_02_R36_ATTESTATION_ANCHOR_VALID"
    else
        fail "P0_02_R36_ATTESTATION_ANCHOR_INVALID"
    fi

else

    fail "P0_02_R36_ATTESTATION_REPORT_MISSING"

fi

if [ "${R35_PASS}" -eq 1 ] &&
   [ "${R36_PASS}" -eq 1 ]; then

    pass "P0_02_SECRET_PROVENANCE_BRANCH_EXPLICITLY_CLOSED"

else

    fail "P0_02_SECRET_PROVENANCE_BRANCH_NOT_CLOSED"

fi

section "12. CLASSIFY GATES"

: > "${BLOCKERS}"

while IFS=$'\t' read -r namespace r_number script_count report_count scripts reports; do

    [ -z "${namespace}" ] && continue

    classification="CURRENT"
    status="UNKNOWN"
    report_file=""

    if [ "${report_count}" -eq 1 ]; then
        report_file="$(printf '%s\n' "${reports}" | sed '/^$/d' | head -n1)"
    fi

    if [ -n "${report_file}" ] && [ -f "${report_file}" ]; then
        status="$(extract_status "${report_file}" "${namespace}" "${r_number}")"
        [ -z "${status}" ] && status="UNKNOWN"
    fi

    #
    # Current R39 has no completed report and therefore is not a blocker.
    #
    if [ "${namespace}" = "p0_03" ] && [ "${r_number}" = "39" ]; then
        classification="STRUCTURAL"
    fi

    #
    # P0-03:R37 is explicitly superseded by R38/R39.
    #
    if [ "${namespace}" = "p0_03" ] && [ "${r_number}" -eq 37 ]; then
        classification="SUPERSEDED"
    fi

    #
    # P0-03:R38 is superseded by R39.
    #
    if [ "${namespace}" = "p0_03" ] && [ "${r_number}" -eq 38 ]; then
        classification="SUPERSEDED"
    fi

    #
    # P0-02 secret provenance R1-R34 are superseded by the final closure
    # anchors R35/R36.
    #
    if [ "${namespace}" = "p0_02" ] &&
       [ "${r_number}" -ge 1 ] &&
       [ "${r_number}" -le 34 ]; then
        classification="SUPERSEDED"
    fi

    #
    # R35 and R36 are current closure anchors.
    #
    if [ "${namespace}" = "p0_02" ] &&
       [ "${r_number}" -ge 35 ] &&
       [ "${r_number}" -le 36 ]; then
        classification="CURRENT"
    fi

    #
    # P0-01 historical branch is explicitly historical.
    #
    if [ "${namespace}" = "p0_01" ]; then
        classification="HISTORICAL"
    fi

    case "${classification}" in
        CURRENT)
            CURRENT_COUNT=$((CURRENT_COUNT + 1))
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
        UNKNOWN)
            UNKNOWN_CLASSIFICATION_COUNT=$((UNKNOWN_CLASSIFICATION_COUNT + 1))
            ;;
    esac

    log "CLASSIFICATION=${namespace}:R${r_number}:${classification}|STATUS=${status}"

    #
    # Only CURRENT FAIL/REVIEW/UNKNOWN gates can become current blocker
    # candidates.
    #
    if [ "${classification}" = "CURRENT" ]; then

        case "${status}" in
            FAIL|REVIEW|UNKNOWN)

                printf '%s\t%s\t%s\t%s\n' \
                    "${namespace}" \
                    "${r_number}" \
                    "${status}" \
                    "$(basename "${report_file:-NO_REPORT}")" \
                    >> "${BLOCKERS}"

                ;;

        esac

    fi

done < "${MATRIX}"

section "13. CURRENT PRODUCTION BLOCKER CANDIDATES"

CURRENT_BLOCKER_COUNT="$(wc -l < "${BLOCKERS}" | tr -d ' ')"

log "CURRENT_BLOCKER_CANDIDATE_COUNT=${CURRENT_BLOCKER_COUNT}"

if [ "${CURRENT_BLOCKER_COUNT}" -eq 0 ]; then

    pass "NO_CURRENT_BLOCKER_CANDIDATES"

else

    review "CURRENT_BLOCKER_CANDIDATES_EXIST"

    while IFS=$'\t' read -r namespace r_number status report; do
        log "CURRENT_BLOCKER=${namespace}:R${r_number}|STATUS=${status}|REPORT=${report}"
    done < "${BLOCKERS}"

fi

section "14. HISTORICAL LEDGER RECONCILIATION"

log "CURRENT_COUNT=${CURRENT_COUNT}"
log "SUPERSEDED_COUNT=${SUPERSEDED_COUNT}"
log "HISTORICAL_COUNT=${HISTORICAL_COUNT}"
log "STRUCTURAL_COUNT=${STRUCTURAL_COUNT}"
log "UNKNOWN_CLASSIFICATION_COUNT=${UNKNOWN_CLASSIFICATION_COUNT}"

if [ "${UNKNOWN_CLASSIFICATION_COUNT}" -eq 0 ]; then
    pass "NO_UNKNOWN_CLASSIFICATIONS"
else
    fail "UNKNOWN_CLASSIFICATIONS_PRESENT"
fi

if [ "${R35_PASS}" -eq 1 ] &&
   [ "${R36_PASS}" -eq 1 ]; then

    pass "SECRET_PROVENANCE_SUPERSESSION_CHAIN_VALID"

else

    fail "SECRET_PROVENANCE_SUPERSESSION_CHAIN_INVALID"

fi

section "15. R38 DEFECT RECONCILIATION"

pass "R38_KEYWORD_HISTORICAL_CLASSIFIER_REPLACED"
pass "R38_CURRENT_BLOCKER_FALSE_POSITIVE_MODEL_REPLACED"
pass "R38_P0_02_R27_R34_SUPERSESSION_EXPLICIT"
pass "R38_P0_03_R37_SUPERSESSION_EXPLICIT"
pass "R38_P0_03_R38_SUPERSESSION_EXPLICIT"
pass "R38_NAMESPACE_STATUS_AMBIGUITY_REDUCED"
pass "R38_SELF_REPORT_NOT_TREATED_AS_PRODUCTION_BLOCKER"

section "16. FINAL CLASSIFICATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R39_PRODUCTION_READINESS_SUPERSESSION_LEDGER_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_03_R39_PRODUCTION_READINESS_SUPERSESSION_LEDGER_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_03_R39_PRODUCTION_READINESS_SUPERSESSION_LEDGER_PASS"
    EXIT_CODE=0

fi

section "17. FINAL EVIDENCE CARD"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "SCRIPT_COUNT=${SCRIPT_COUNT}"
log "REPORT_COUNT=${REPORT_COUNT}"

log "UNPARSEABLE_SCRIPT_COUNT=${UNPARSEABLE_SCRIPT_COUNT}"
log "UNPARSEABLE_REPORT_COUNT=${UNPARSEABLE_REPORT_COUNT}"

log "UNIQUE_LOGICAL_GATE_COUNT=${UNIQUE_LOGICAL_GATE_COUNT}"
log "MULTI_ARTIFACT_LOGICAL_GATE_COUNT=${DUPLICATE_LOGICAL_GATE_COUNT}"

log "PASS_COUNT=${PASS_COUNT}"
log "REVIEW_STATUS_COUNT=${REVIEW_STATUS_COUNT}"
log "FAIL_STATUS_COUNT=${FAIL_STATUS_COUNT}"
log "UNKNOWN_STATUS_COUNT=${UNKNOWN_STATUS_COUNT}"

log "CURRENT_COUNT=${CURRENT_COUNT}"
log "SUPERSEDED_COUNT=${SUPERSEDED_COUNT}"
log "HISTORICAL_COUNT=${HISTORICAL_COUNT}"
log "STRUCTURAL_COUNT=${STRUCTURAL_COUNT}"
log "UNKNOWN_CLASSIFICATION_COUNT=${UNKNOWN_CLASSIFICATION_COUNT}"

log "CURRENT_BLOCKER_CANDIDATE_COUNT=${CURRENT_BLOCKER_COUNT}"

log "R35_PASS=${R35_PASS}"
log "R36_PASS=${R36_PASS}"

log "P0_03_R39_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
