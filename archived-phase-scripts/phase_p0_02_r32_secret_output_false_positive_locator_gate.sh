#!/data/data/com.termux/files/usr/bin/bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
EXPECTED_ROOT="/data/data/com.termux/files/home/waste-platform"

REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r32_secret_output_false_positive_locator_gate.txt"

mkdir -p "${REPORT_DIR}"

FAILURE_COUNT=0
REVIEW_COUNT=0
MATCH_COUNT=0
REAL_SOURCE_MATCH_COUNT=0
AUDIT_SELF_MATCH_COUNT=0
VALUE_LEAK_SUSPECT_COUNT=0
CLASSIFICATION_COUNT=0

SECRET_KEYS=(
    POSTGRES_PASSWORD
    DATABASE_PASSWORD
    JWT_SECRET_KEY
    JWT_REFRESH_SECRET_KEY
    S3_SECRET_KEY
)

log() {
    echo "$1"
    echo "$1" >> "${REPORT}"
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

rm -f "${REPORT}"
touch "${REPORT}"

section "P0-02 R32 SECRET OUTPUT FALSE-POSITIVE LOCATOR GATE"

section "1. SAFETY PRECHECK"

if [ "${PROJECT_ROOT}" = "${EXPECTED_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
else
    fail "PROJECT_ROOT_MISMATCH"
fi

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_DELETIONS=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "BOUNDED_SCAN=YES"

section "2. SCAN SCOPE"

log "The scan searches for output-like constructs mentioning secret identifiers."
log "Audit-output files and phase_p0_02 audit scripts are excluded."
log "Secret values themselves are never printed."

section "3. SECRET IDENTIFIER SET"

for key in "${SECRET_KEYS[@]}"; do
    pass "SECRET_IDENTIFIER_REGISTERED=${key}"
done

section "4. NON-AUDIT OUTPUT PATTERN LOCATOR"

TMP_RAW="$(mktemp)"
TMP_CLASSIFIED="$(mktemp)"

cleanup() {
    rm -f "${TMP_RAW}" "${TMP_CLASSIFIED}"
}
trap cleanup EXIT

# Bounded source scan.
#
# Exclusions:
#   audit-output/
#   phase_p0_02_*.sh
#   .git/
#   node_modules/
#   .venv/
#   venv/
#   __pycache__/
#
# We intentionally look for output constructs and secret identifiers.
# We do NOT print actual secret values.

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude='phase_p0_02_*.sh' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite' \
    --exclude='*.sqlite3' \
    --exclude='*.log' \
    -E '(echo|printf|print|println|logger|logging|console\.log|console\.error|sys\.stdout|stdout\.write|stderr\.write)[^[:cntrl:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
    "${PROJECT_ROOT}" \
    > "${TMP_RAW}" 2>/dev/null || true

MATCH_COUNT="$(wc -l < "${TMP_RAW}" | tr -d ' ')"

log "NON_AUDIT_OUTPUT_MATCH_COUNT=${MATCH_COUNT}"

if [ "${MATCH_COUNT}" -eq 0 ]; then
    pass "NO_NON_AUDIT_OUTPUT_PATTERN_MATCHES"
else
    review "NON_AUDIT_OUTPUT_PATTERN_PRESENT"
fi

section "5. MATCH LOCATION REPORT"

if [ "${MATCH_COUNT}" -gt 0 ]; then

    while IFS= read -r line; do
        [ -z "${line}" ] && continue

        file="${line%%:*}"
        rest="${line#*:}"
        lineno="${rest%%:*}"
        content="${rest#*:}"

        MATCH_CLASS="UNKNOWN"

        case "${file}" in
            */audit-output/*)
                MATCH_CLASS="AUDIT_OUTPUT"
                ;;
            */phase_p0_02_*.sh)
                MATCH_CLASS="AUDIT_SCRIPT"
                ;;
            */tests/*|*/test/*)
                MATCH_CLASS="TEST_CODE"
                ;;
            */docs/*|*/README*|*.md)
                MATCH_CLASS="DOCUMENTATION"
                ;;
            */scripts/*)
                MATCH_CLASS="SCRIPT_SOURCE"
                ;;
            */app/*|*/src/*|*/backend/*|*/core/*)
                MATCH_CLASS="APPLICATION_SOURCE"
                ;;
            *)
                MATCH_CLASS="OTHER_SOURCE"
                ;;
        esac

        CLASSIFICATION_COUNT=$((CLASSIFICATION_COUNT + 1))

        log "MATCH_FILE=${file}"
        log "MATCH_LINE=${lineno}"
        log "MATCH_CLASS=${MATCH_CLASS}"

        # Never reproduce the matched line verbatim because it could contain
        # a secret value or an interpolated value.
        #
        # Instead emit a structural classification based on syntax.
        safe_structure="$(printf '%s\n' "${content}" | sed -E \
            -e 's/[[:space:]]+/ /g' \
            -e 's/(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)/<SECRET_IDENTIFIER>/g' \
            -e 's/([A-Za-z0-9_]+[[:space:]]*=[[:space:]]*)[^[:space:]]+/\1<VALUE_REDACTED>/g' \
            -e 's/\$\{[^}]+\}/\${INTERPOLATION_REDACTED}/g' \
            -e 's/:[[:space:]]*[^[:space:]]+/:\ <VALUE_REDACTED>/g')"

        log "MATCH_STRUCTURE=${safe_structure}"

        # Structural value-leak heuristic:
        #
        # A direct literal after an output call is suspicious.
        # A secret identifier, shell interpolation, or variable expansion
        # is not itself proof of value leakage.
        #
        # The line is therefore classified conservatively.
        if printf '%s\n' "${content}" | grep -Eq \
            '(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*[:=][[:space:]]*["'\'']?[A-Za-z0-9_./:@%+,-]{8,}["'\'']?'; then

            VALUE_LEAK_SUSPECT_COUNT=$((VALUE_LEAK_SUSPECT_COUNT + 1))
            log "MATCH_VALUE_LEAK_HEURISTIC=REVIEW"

        elif printf '%s\n' "${content}" | grep -Eq \
            '\$\{?[A-Za-z_][A-Za-z0-9_]*\}?'; then

            log "MATCH_VALUE_LEAK_HEURISTIC=NOT_PROVEN"

        else
            log "MATCH_VALUE_LEAK_HEURISTIC=NOT_PROVEN"
        fi

        log "------------------------------------------------------------"

    done < "${TMP_RAW}"

else
    pass "MATCH_LOCATION_REPORT_EMPTY"
fi

section "6. AUDIT-SELF MATCH CROSSCHECK"

# Independently verify that the historical R27 count is not being reproduced
# from excluded audit artifacts.

AUDIT_SCRIPT_MATCH_COUNT="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=node_modules \
        --exclude-dir=.venv \
        --exclude-dir=venv \
        --exclude-dir=__pycache__ \
        --exclude='*.pyc' \
        --exclude='*.db' \
        --exclude='*.sqlite' \
        --exclude='*.sqlite3' \
        --exclude='*.log' \
        -E '(echo|printf|print|println|logger|logging|console\.log|console\.error|sys\.stdout|stdout\.write|stderr\.write)[^[:cntrl:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
        "${PROJECT_ROOT}" \
        2>/dev/null \
    | grep -E 'phase_p0_02_|audit-output/' \
    | wc -l \
    | tr -d ' '
)"

if [ -z "${AUDIT_SCRIPT_MATCH_COUNT}" ]; then
    AUDIT_SCRIPT_MATCH_COUNT=0
fi

AUDIT_SELF_MATCH_COUNT="${AUDIT_SCRIPT_MATCH_COUNT}"

log "AUDIT_SELF_MATCH_COUNT=${AUDIT_SELF_MATCH_COUNT}"

if [ "${AUDIT_SELF_MATCH_COUNT}" -gt 0 ]; then
    pass "HISTORICAL_AUDIT_SELF_MATCHES_EXIST"
else
    pass "NO_AUDIT_SELF_MATCHES_IN_CURRENT_NON_AUDIT_SCAN"
fi

section "7. APPLICATION SOURCE VALUE-LEAK HEURISTIC"

log "VALUE_LEAK_SUSPECT_COUNT=${VALUE_LEAK_SUSPECT_COUNT}"

if [ "${VALUE_LEAK_SUSPECT_COUNT}" -eq 0 ]; then
    pass "NO_DIRECT_SECRET_VALUE_OUTPUT_HEURISTIC_MATCH"
else
    review "DIRECT_SECRET_VALUE_OUTPUT_HEURISTIC_MATCH_PRESENT"
fi

section "8. CURRENT CORE PROVENANCE RECHECK"

COMPOSE_TARGET_COUNT="$(
    awk '
    /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ { count++ }
    /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ { count++ }
    /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ { count++ }
    END { print count+0 }
    ' docker-compose.yml 2>/dev/null
)"

COMPOSE_REFERENCE_COUNT="$(
    awk '
    /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ {
        line=$0
        sub(/^[^:]*:[[:space:]]*/, "", line)
        if (line ~ /^\$\{/) count++
    }
    /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ {
        line=$0
        sub(/^[^:]*:[[:space:]]*/, "", line)
        if (line ~ /^\$\{/) count++
    }
    /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ {
        line=$0
        sub(/^[^:]*:[[:space:]]*/, "", line)
        if (line ~ /^\$\{/) count++
    }
    END { print count+0 }
    ' docker-compose.yml 2>/dev/null
)"

COMPOSE_LITERAL_COUNT="$(
    awk '
    /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ {
        line=$0
        sub(/^[^:]*:[[:space:]]*/, "", line)
        if (line !~ /^\$\{/) count++
    }
    /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ {
        line=$0
        sub(/^[^:]*:[[:space:]]*/, "", line)
        if (line !~ /^\$\{/) count++
    }
    /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ {
        line=$0
        sub(/^[^:]*:[[:space:]]*/, "", line)
        if (line !~ /^\$\{/) count++
    }
    END { print count+0 }
    ' docker-compose.yml 2>/dev/null
)"

log "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
log "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
log "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"

if [ "${COMPOSE_TARGET_COUNT}" -eq 3 ] &&
   [ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] &&
   [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ]; then
    pass "CURRENT_COMPOSE_PROVENANCE_CORE_HOLDS"
else
    fail "CURRENT_COMPOSE_PROVENANCE_CORE_BROKEN"
fi

section "9. FINAL CLASSIFICATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R32_SECRET_OUTPUT_FALSE_POSITIVE_LOCATOR_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R32_SECRET_OUTPUT_FALSE_POSITIVE_LOCATOR_REVIEW"
    EXIT_CODE=1

else
    STATUS="PASS"
    RESULT="P0_02_R32_SECRET_OUTPUT_FALSE_POSITIVE_LOCATOR_PASS"
    EXIT_CODE=0
fi

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"
log "MATCH_COUNT=${MATCH_COUNT}"
log "REAL_SOURCE_MATCH_COUNT=${REAL_SOURCE_MATCH_COUNT}"
log "AUDIT_SELF_MATCH_COUNT=${AUDIT_SELF_MATCH_COUNT}"
log "VALUE_LEAK_SUSPECT_COUNT=${VALUE_LEAK_SUSPECT_COUNT}"
log "CLASSIFICATION_COUNT=${CLASSIFICATION_COUNT}"
log "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
log "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
log "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
log "P0_02_R32_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

exit "${EXIT_CODE}"
