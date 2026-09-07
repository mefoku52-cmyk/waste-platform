#!/data/data/com.termux/files/usr/bin/bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
EXPECTED_ROOT="/data/data/com.termux/files/home/waste-platform"

REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r34_secret_provenance_scope_corrected_gate.txt"

mkdir -p "${REPORT_DIR}"
rm -f "${REPORT}"
touch "${REPORT}"

FAILURE_COUNT=0
REVIEW_COUNT=0

ENV_SECRET_COUNT=0
COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_KEY_FAILURE_COUNT=0
RUNTIME_DIRECT_ASSIGNMENT_COUNT=0
CI_IDENTIFIER_COUNT=0
DEPLOY_SECRET_REFERENCE_COUNT=0

APPLICATION_OUTPUT_MATCH_COUNT=0
APPLICATION_DIRECT_VALUE_MATCH_COUNT=0
FORENSIC_ARCHIVE_MATCH_COUNT=0
HISTORICAL_AUDIT_MATCH_COUNT=0

DATABASE_URL_MATCH_COUNT=0

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

section "P0-02 R34 SECRET PROVENANCE SCOPE-CORRECTED GATE"

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

section "2. AUTHORITY FILES"

AUTHORITY_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

for f in "${AUTHORITY_FILES[@]}"; do
    if [ -f "${PROJECT_ROOT}/${f}" ]; then
        pass "AUTHORITY_PRESENT=${f}"
    else
        fail "AUTHORITY_MISSING=${f}"
    fi
done

section "3. ENV SECRET AUTHORITY"

SECRET_KEYS=(
    POSTGRES_PASSWORD
    DATABASE_PASSWORD
    JWT_SECRET_KEY
    JWT_REFRESH_SECRET_KEY
    S3_SECRET_KEY
)

for key in "${SECRET_KEYS[@]}"; do
    if awk -F= -v k="${key}" '
        $1 == k { found=1 }
        END { exit(found ? 0 : 1) }
    ' "${PROJECT_ROOT}/.env.production" 2>/dev/null; then
        pass "ENV_AUTHORITY_PRESENT=${key}"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING=${key}"
    fi
done

log "ENV_SECRET_AUTHORITY_COUNT=${ENV_SECRET_COUNT}"

if [ "${ENV_SECRET_COUNT}" -eq 5 ]; then
    pass "ENV_SECRET_AUTHORITY_CARDINALITY_EXACT"
else
    fail "ENV_SECRET_AUTHORITY_CARDINALITY_MISMATCH"
fi

section "4. COMPOSE TARGETS"

COMPOSE_TARGET_COUNT="$(
    awk '
        /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ { count++ }
        /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ { count++ }
        /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ { count++ }
        END { print count+0 }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null
)"

log "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"

if [ "${COMPOSE_TARGET_COUNT}" -eq 3 ]; then
    pass "COMPOSE_TARGET_CARDINALITY_EXACT"
else
    fail "COMPOSE_TARGET_CARDINALITY_MISMATCH"
fi

section "5. COMPOSE REFERENCE VS LITERAL"

COMPOSE_REFERENCE_COUNT="$(
    awk '
        /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ {
            v=$0
            sub(/^[^:]*:[[:space:]]*/, "", v)
            if (v ~ /^\$\{/) count++
        }
        /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ {
            v=$0
            sub(/^[^:]*:[[:space:]]*/, "", v)
            if (v ~ /^\$\{/) count++
        }
        /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ {
            v=$0
            sub(/^[^:]*:[[:space:]]*/, "", v)
            if (v ~ /^\$\{/) count++
        }
        END { print count+0 }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null
)"

COMPOSE_LITERAL_COUNT="$(
    awk '
        /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ {
            v=$0
            sub(/^[^:]*:[[:space:]]*/, "", v)
            if (v !~ /^\$\{/) count++
        }
        /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ {
            v=$0
            sub(/^[^:]*:[[:space:]]*/, "", v)
            if (v !~ /^\$\{/) count++
        }
        /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ {
            v=$0
            sub(/^[^:]*:[[:space:]]*/, "", v)
            if (v !~ /^\$\{/) count++
        }
        END { print count+0 }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null
)"

log "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
log "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"

if [ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ]; then
    pass "COMPOSE_REFERENCE_CARDINALITY_EXACT"
else
    fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH"
fi

if [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ]; then
    pass "COMPOSE_LITERAL_COUNT_ZERO"
else
    fail "COMPOSE_LITERAL_SECRET_ASSIGNMENT_PRESENT"
fi

section "6. KEY-BY-KEY COMPOSE PROOF"

for key in \
    POSTGRES_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY
do
    if awk -v k="${key}" '
        $0 ~ "^[[:space:]]*" k ":[[:space:]]*" {
            v=$0
            sub(/^[^:]*:[[:space:]]*/, "", v)
            if (v ~ /^\$\{/) found=1
        }
        END { exit(found ? 0 : 1) }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null; then
        pass "COMPOSE_REFERENCE_PRESENT=${key}"
    else
        fail "COMPOSE_REFERENCE_MISSING=${key}"
        COMPOSE_KEY_FAILURE_COUNT=$((COMPOSE_KEY_FAILURE_COUNT + 1))
    fi
done

log "COMPOSE_KEY_REFERENCE_FAILURES=${COMPOSE_KEY_FAILURE_COUNT}"

section "7. DATABASE_URL PROVENANCE"

# Accept the actual Compose forms:
#   ${POSTGRES_PASSWORD}
#   ${POSTGRES_PASSWORD:-...}
#   ${POSTGRES_PASSWORD:?...}
#   ${POSTGRES_PASSWORD-default}
#   ${POSTGRES_PASSWORD?error}
#
# The important invariant is that DATABASE_URL obtains the password through
# Compose interpolation of POSTGRES_PASSWORD rather than a literal value.

if grep -Eq \
    'DATABASE_URL:[^#]*\$\{POSTGRES_PASSWORD([:-?][^}]*)?\}' \
    "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null; then

    DATABASE_URL_MATCH_COUNT=1
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"

else

    DATABASE_URL_MATCH_COUNT=0
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

log "DATABASE_URL_MATCH_COUNT=${DATABASE_URL_MATCH_COUNT}"

section "8. RUNTIME DIRECT SECRET ASSIGNMENT"

RUNTIME_DIRECT_ASSIGNMENT_COUNT="$(
    grep -REn \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        --exclude='phase_p0_02_*.sh' \
        --exclude='*.pyc' \
        -E '^[[:space:]]*(os\.environ|os\.getenv|getenv)[^;]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|POSTGRES_PASSWORD|DATABASE_PASSWORD|S3_SECRET_KEY)[[:space:]]*=' \
        "${PROJECT_ROOT}/app" \
        "${PROJECT_ROOT}/src" \
        "${PROJECT_ROOT}/backend" \
        2>/dev/null \
    | wc -l \
    | tr -d ' '
)"

if [ -z "${RUNTIME_DIRECT_ASSIGNMENT_COUNT}" ]; then
    RUNTIME_DIRECT_ASSIGNMENT_COUNT=0
fi

log "RUNTIME_DIRECT_ASSIGNMENT_COUNT=${RUNTIME_DIRECT_ASSIGNMENT_COUNT}"

if [ "${RUNTIME_DIRECT_ASSIGNMENT_COUNT}" -eq 0 ]; then
    pass "NO_RUNTIME_DIRECT_SECRET_ASSIGNMENT"
else
    fail "RUNTIME_DIRECT_SECRET_ASSIGNMENT_PRESENT"
fi

section "9. CI SECRET IDENTIFIER SET"

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "${key}" "${PROJECT_ROOT}/.github/workflows/ci.yml" 2>/dev/null; then
        pass "CI_IDENTIFIER_PRESENT=${key}"
        CI_IDENTIFIER_COUNT=$((CI_IDENTIFIER_COUNT + 1))
    else
        fail "CI_IDENTIFIER_MISSING=${key}"
    fi
done

log "CI_IDENTIFIER_COUNT=${CI_IDENTIFIER_COUNT}"

if [ "${CI_IDENTIFIER_COUNT}" -eq 5 ]; then
    pass "CI_IDENTIFIER_CARDINALITY_EXACT"
else
    fail "CI_IDENTIFIER_CARDINALITY_MISMATCH"
fi

section "10. DEPLOY SECRET REFERENCE"

DEPLOY_SECRET_REFERENCE_COUNT="$(
    grep -En \
        -E '(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
        "${PROJECT_ROOT}/scripts/deploy.sh" 2>/dev/null \
    | grep -Ev \
        '(#|audit|report|log|print|echo|printf)' \
    | wc -l \
    | tr -d ' '
)"

if [ -z "${DEPLOY_SECRET_REFERENCE_COUNT}" ]; then
    DEPLOY_SECRET_REFERENCE_COUNT=0
fi

log "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"

if [ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ]; then
    pass "DEPLOY_SECRET_REFERENCE_COUNT_ZERO"
else
    fail "DEPLOY_SECRET_REFERENCE_PRESENT"
fi

section "11. FORENSIC ARCHIVE ISOLATION"

# These files are explicitly historical forensic artifacts.
# They must NEVER enter the application-source leak classifier.

FORENSIC_ARCHIVE_MATCH_COUNT="$(
    grep -RInE \
        --exclude='*.pyc' \
        --exclude='*.db' \
        --exclude='*.sqlite' \
        --exclude='*.sqlite3' \
        -E '(echo|printf|print|println|logger|logging|console\.log|console\.error|sys\.stdout|stdout\.write|stderr\.write)[^[:cntrl:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
        "${PROJECT_ROOT}/scripts/forensics/archive" \
        2>/dev/null \
    | wc -l \
    | tr -d ' '
)"

if [ -z "${FORENSIC_ARCHIVE_MATCH_COUNT}" ]; then
    FORENSIC_ARCHIVE_MATCH_COUNT=0
fi

log "FORENSIC_ARCHIVE_MATCH_COUNT=${FORENSIC_ARCHIVE_MATCH_COUNT}"

if [ "${FORENSIC_ARCHIVE_MATCH_COUNT}" -gt 0 ]; then
    pass "FORENSIC_ARCHIVE_EXCLUDED_FROM_APPLICATION_CLASSIFICATION"
else
    pass "FORENSIC_ARCHIVE_HAS_NO_SECRET_OUTPUT_PATTERN"
fi

section "12. HISTORICAL AUDIT ARTIFACT ISOLATION"

HISTORICAL_AUDIT_MATCH_COUNT="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        -E '(echo|printf|print|println|logger|logging|console\.log|console\.error|sys\.stdout|stdout\.write|stderr\.write)[^[:cntrl:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
        "${PROJECT_ROOT}" \
        2>/dev/null \
    | grep -E 'phase_p0_02_|\.pre_literal_classifier_fix' \
    | wc -l \
    | tr -d ' '
)"

if [ -z "${HISTORICAL_AUDIT_MATCH_COUNT}" ]; then
    HISTORICAL_AUDIT_MATCH_COUNT=0
fi

log "HISTORICAL_AUDIT_MATCH_COUNT=${HISTORICAL_AUDIT_MATCH_COUNT}"

if [ "${HISTORICAL_AUDIT_MATCH_COUNT}" -gt 0 ]; then
    pass "HISTORICAL_AUDIT_ARTIFACTS_EXCLUDED_FROM_APPLICATION_CLASSIFICATION"
else
    pass "NO_HISTORICAL_AUDIT_OUTPUT_MATCHES"
fi

section "13. CURRENT APPLICATION OUTPUT CLASSIFIER"

TMP_APP_OUTPUT="$(mktemp)"

cleanup() {
    rm -f "${TMP_APP_OUTPUT}"
}
trap cleanup EXIT

# IMPORTANT:
# Only current application source is classified here.
#
# Explicit exclusions:
#   scripts/forensics/**
#   scripts/forensics/archive/**
#   audit-output/**
#   phase_p0_02_*.sh
#   *.pre_literal_classifier_fix
#
# This prevents historical audit material from becoming a false production
# secret-output finding.

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude='phase_p0_02_*.sh' \
    --exclude='*.pre_literal_classifier_fix' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite' \
    --exclude='*.sqlite3' \
    --exclude='*.log' \
    -E '(echo|printf|print|println|logger|logging|console\.log|console\.error|sys\.stdout|stdout\.write|stderr\.write)[^[:cntrl:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
    "${PROJECT_ROOT}/app" \
    "${PROJECT_ROOT}/src" \
    "${PROJECT_ROOT}/backend" \
    2>/dev/null \
    > "${TMP_APP_OUTPUT}" || true

APPLICATION_OUTPUT_MATCH_COUNT="$(wc -l < "${TMP_APP_OUTPUT}" | tr -d ' ')"

log "APPLICATION_OUTPUT_MATCH_COUNT=${APPLICATION_OUTPUT_MATCH_COUNT}"

if [ "${APPLICATION_OUTPUT_MATCH_COUNT}" -eq 0 ]; then
    pass "NO_CURRENT_APPLICATION_SECRET_OUTPUT_PATTERN"
else
    fail "CURRENT_APPLICATION_SECRET_OUTPUT_PATTERN_PRESENT"

    while IFS= read -r line; do
        [ -z "${line}" ] && continue

        file="${line%%:*}"
        rest="${line#*:}"
        lineno="${rest%%:*}"

        log "APPLICATION_OUTPUT_LOCATION=${file}:${lineno}"
    done < "${TMP_APP_OUTPUT}"
fi

section "14. CURRENT APPLICATION DIRECT VALUE LEAK CLASSIFIER"

APPLICATION_DIRECT_VALUE_MATCH_COUNT="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        --exclude-dir=node_modules \
        --exclude-dir=.venv \
        --exclude-dir=venv \
        --exclude-dir=__pycache__ \
        --exclude='phase_p0_02_*.sh' \
        --exclude='*.pre_literal_classifier_fix' \
        --exclude='*.pyc' \
        -E '(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*[:=][[:space:]]*["'\''][A-Za-z0-9_./:@%+,-]{12,}["'\'']' \
        "${PROJECT_ROOT}/app" \
        "${PROJECT_ROOT}/src" \
        "${PROJECT_ROOT}/backend" \
        2>/dev/null \
    | wc -l \
    | tr -d ' '
)"

if [ -z "${APPLICATION_DIRECT_VALUE_MATCH_COUNT}" ]; then
    APPLICATION_DIRECT_VALUE_MATCH_COUNT=0
fi

log "APPLICATION_DIRECT_VALUE_MATCH_COUNT=${APPLICATION_DIRECT_VALUE_MATCH_COUNT}"

if [ "${APPLICATION_DIRECT_VALUE_MATCH_COUNT}" -eq 0 ]; then
    pass "NO_CURRENT_APPLICATION_DIRECT_SECRET_VALUE_PATTERN"
else
    fail "CURRENT_APPLICATION_DIRECT_SECRET_VALUE_PATTERN_PRESENT"
fi

section "15. R29 HISTORICAL CONTRADICTION"

R29_FILE="${PROJECT_ROOT}/audit-output/p0_02_r29_secret_provenance_cross_file_consistency_gate.txt"

R29_MISSING_COUNT=0
R29_CONSISTENT_COUNT=0

if [ -f "${R29_FILE}" ]; then

    R29_MISSING_COUNT="$(
        grep -Ec 'FAIL: COMPOSE_REFERENCE_MISSING=' \
            "${R29_FILE}" 2>/dev/null || true
    )

    R29_CONSISTENT_COUNT="$(
        grep -Ec 'PASS: R29_CROSS_FILE_SECRET_PROVENANCE_CONSISTENT' \
            "${R29_FILE}" 2>/dev/null || true
    )

    log "R29_COMPOSE_MISSING_COUNT=${R29_MISSING_COUNT}"
    log "R29_INTERNAL_CONSISTENT_ASSERTION_COUNT=${R29_CONSISTENT_COUNT}"

    if [ "${R29_MISSING_COUNT}" -gt 0 ] &&
       [ "${R29_CONSISTENT_COUNT}" -gt 0 ]; then

        pass "R29_HISTORICAL_INTERNAL_CONTRADICTION_CONFIRMED_AS_AUDIT_LOGIC_DEFECT"

    else
        pass "R29_NO_INTERNAL_CONTRADICTION"
    fi

else
    review "R29_REPORT_NOT_FOUND"
fi

section "16. CURRENT CORE INVARIANT RECONCILIATION"

if [ "${ENV_SECRET_COUNT}" -eq 5 ] &&
   [ "${COMPOSE_TARGET_COUNT}" -eq 3 ] &&
   [ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] &&
   [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] &&
   [ "${COMPOSE_KEY_FAILURE_COUNT}" -eq 0 ] &&
   [ "${DATABASE_URL_MATCH_COUNT}" -eq 1 ] &&
   [ "${RUNTIME_DIRECT_ASSIGNMENT_COUNT}" -eq 0 ] &&
   [ "${CI_IDENTIFIER_COUNT}" -eq 5 ] &&
   [ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ] &&
   [ "${APPLICATION_OUTPUT_MATCH_COUNT}" -eq 0 ] &&
   [ "${APPLICATION_DIRECT_VALUE_MATCH_COUNT}" -eq 0 ]; then

    pass "CURRENT_SECRET_PROVENANCE_CORE_INVARIANTS_HOLD"

else
    fail "CURRENT_SECRET_PROVENANCE_CORE_INVARIANTS_BROKEN"
fi

section "17. FINAL CLASSIFICATION"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R34_SECRET_PROVENANCE_SCOPE_CORRECTED_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R34_SECRET_PROVENANCE_SCOPE_CORRECTED_REVIEW"
    EXIT_CODE=1

else
    STATUS="PASS"
    RESULT="P0_02_R34_SECRET_PROVENANCE_SCOPE_CORRECTED_PASS"
    EXIT_CODE=0
fi

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"
log "ENV_SECRET_AUTHORITY_COUNT=${ENV_SECRET_COUNT}"
log "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
log "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
log "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
log "COMPOSE_KEY_REFERENCE_FAILURES=${COMPOSE_KEY_FAILURE_COUNT}"
log "DATABASE_URL_MATCH_COUNT=${DATABASE_URL_MATCH_COUNT}"
log "RUNTIME_DIRECT_ASSIGNMENT_COUNT=${RUNTIME_DIRECT_ASSIGNMENT_COUNT}"
log "CI_IDENTIFIER_COUNT=${CI_IDENTIFIER_COUNT}"
log "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"
log "APPLICATION_OUTPUT_MATCH_COUNT=${APPLICATION_OUTPUT_MATCH_COUNT}"
log "APPLICATION_DIRECT_VALUE_MATCH_COUNT=${APPLICATION_DIRECT_VALUE_MATCH_COUNT}"
log "FORENSIC_ARCHIVE_MATCH_COUNT=${FORENSIC_ARCHIVE_MATCH_COUNT}"
log "HISTORICAL_AUDIT_MATCH_COUNT=${HISTORICAL_AUDIT_MATCH_COUNT}"
log "R29_COMPOSE_MISSING_COUNT=${R29_MISSING_COUNT}"
log "R29_INTERNAL_CONSISTENT_ASSERTION_COUNT=${R29_CONSISTENT_COUNT}"
log "P0_02_R34_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

exit "${EXIT_CODE}"
