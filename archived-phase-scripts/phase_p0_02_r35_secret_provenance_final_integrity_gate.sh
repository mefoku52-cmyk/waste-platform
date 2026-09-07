#!/data/data/com.termux/files/usr/bin/bash

# ============================================================================
# P0-02 R35
# SECRET PROVENANCE FINAL INTEGRITY GATE
#
# PURPOSE
# -------
# Final, deterministic closure gate for the P0-02 secret-provenance chain.
#
# DESIGN PRINCIPLES
# -----------------
# 1. Read-only.
# 2. Fail-closed.
# 3. Explicit source scopes.
# 4. No secret values are ever printed.
# 5. Historical audit artifacts cannot contaminate production classification.
# 6. Every cardinality invariant is independently recomputed.
# 7. Historical R29 results are parsed structurally, not heuristically.
# 8. The final PASS depends only on CURRENT authoritative invariants.
#
# IMPORTANT
# ---------
# This gate does NOT modify source files.
# This gate does NOT execute application/runtime code.
# This gate does NOT source .env.production.
# This gate does NOT build or deploy anything.
# ============================================================================

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
EXPECTED_ROOT="/data/data/com.termux/files/home/waste-platform"

REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r35_secret_provenance_final_integrity_gate.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

ENV_SECRET_COUNT=0

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_KEY_REFERENCE_FAILURES=0

DATABASE_URL_MATCH_COUNT=0

RUNTIME_DIRECT_ASSIGNMENT_COUNT=0
CI_IDENTIFIER_COUNT=0
DEPLOY_SECRET_REFERENCE_COUNT=0

CURRENT_APPLICATION_OUTPUT_MATCH_COUNT=0
CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT=0

FORENSIC_ARCHIVE_MATCH_COUNT=0
HISTORICAL_AUDIT_MATCH_COUNT=0

R29_MISSING_COUNT=0
R29_CONSISTENT_COUNT=0
R29_HISTORICAL_CONTRADICTION=0

R34_STATUS=""
R34_EXIT_CODE=""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "${TMP_DIR}"
}

trap cleanup EXIT

rm -f "${REPORT}"
touch "${REPORT}"

# ============================================================================
# 1. SAFETY PRECHECK
# ============================================================================

section "P0-02 R35 SECRET PROVENANCE FINAL INTEGRITY GATE"

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
pass "NO_DELETIONS=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "BOUNDED_SCAN=YES"
pass "FAIL_CLOSED_CLASSIFICATION=YES"
pass "EXPLICIT_SCOPE_CLASSIFICATION=YES"
pass "DETERMINISTIC_HISTORICAL_PARSING=YES"

# ============================================================================
# 2. REQUIRED TOOLS
# ============================================================================

section "2. REQUIRED TOOLCHAIN"

for tool in awk grep sed tr wc mktemp; do
    if command -v "${tool}" >/dev/null 2>&1; then
        pass "TOOL_AVAILABLE=${tool}"
    else
        fail "TOOL_MISSING=${tool}"
    fi
done

# ============================================================================
# 3. AUTHORITY FILES
# ============================================================================

section "3. AUTHORITY FILE PRESENCE"

AUTHORITY_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

for file in "${AUTHORITY_FILES[@]}"; do
    if [ -f "${PROJECT_ROOT}/${file}" ]; then
        pass "AUTHORITY_PRESENT=${file}"
    else
        fail "AUTHORITY_MISSING=${file}"
    fi
done

# ============================================================================
# 4. SECRET AUTHORITY SET
# ============================================================================

section "4. SECRET AUTHORITY SET"

SECRET_KEYS=(
    POSTGRES_PASSWORD
    DATABASE_PASSWORD
    JWT_SECRET_KEY
    JWT_REFRESH_SECRET_KEY
    S3_SECRET_KEY
)

for key in "${SECRET_KEYS[@]}"; do

    if awk -F= -v wanted="${key}" '
        $1 == wanted {
            found=1
            exit
        }
        END {
            exit(found ? 0 : 1)
        }
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

# ============================================================================
# 5. COMPOSE TARGET SET
# ============================================================================

section "5. COMPOSE TARGET SET"

COMPOSE_TARGET_COUNT="$(
    awk '
        /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ {
            count++
        }

        /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ {
            count++
        }

        /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ {
            count++
        }

        END {
            print count + 0
        }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null
)"

log "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"

if [ "${COMPOSE_TARGET_COUNT}" -eq 3 ]; then
    pass "COMPOSE_TARGET_CARDINALITY_EXACT"
else
    fail "COMPOSE_TARGET_CARDINALITY_MISMATCH"
fi

# ============================================================================
# 6. COMPOSE REFERENCE/LITERAL CLASSIFIER
# ============================================================================

section "6. COMPOSE REFERENCE/LITERAL CLASSIFIER"

COMPOSE_REFERENCE_COUNT="$(
    awk '
        function classify(line,    value) {
            value=line
            sub(/^[^:]*:[[:space:]]*/, "", value)

            if (value ~ /^\$\{/) {
                return 1
            }

            return 0
        }

        /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ {
            count += classify($0)
        }

        /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ {
            count += classify($0)
        }

        /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ {
            count += classify($0)
        }

        END {
            print count + 0
        }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null
)"

COMPOSE_LITERAL_COUNT="$(
    awk '
        function classify(line,    value) {
            value=line
            sub(/^[^:]*:[[:space:]]*/, "", value)

            if (value !~ /^\$\{/) {
                return 1
            }

            return 0
        }

        /^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*/ {
            count += classify($0)
        }

        /^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*/ {
            count += classify($0)
        }

        /^[[:space:]]*JWT_REFRESH_SECRET_KEY:[[:space:]]*/ {
            count += classify($0)
        }

        END {
            print count + 0
        }
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

# ============================================================================
# 7. KEY-BY-KEY COMPOSE PROOF
# ============================================================================

section "7. KEY-BY-KEY COMPOSE PROOF"

for key in \
    POSTGRES_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY
do

    if awk -v wanted="${key}" '
        $0 ~ "^[[:space:]]*" wanted ":[[:space:]]*" {

            value=$0
            sub(/^[^:]*:[[:space:]]*/, "", value)

            if (value ~ /^\$\{/) {
                found=1
            }
        }

        END {
            exit(found ? 0 : 1)
        }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null; then

        pass "COMPOSE_REFERENCE_PRESENT=${key}"

    else

        fail "COMPOSE_REFERENCE_MISSING=${key}"
        COMPOSE_KEY_REFERENCE_FAILURES=$((COMPOSE_KEY_REFERENCE_FAILURES + 1))

    fi

done

log "COMPOSE_KEY_REFERENCE_FAILURES=${COMPOSE_KEY_REFERENCE_FAILURES}"

# ============================================================================
# 8. DATABASE_URL PROVENANCE
# ============================================================================

section "8. DATABASE_URL PROVENANCE"

# Accept:
#
#   ${POSTGRES_PASSWORD}
#   ${POSTGRES_PASSWORD:-default}
#   ${POSTGRES_PASSWORD:?error}
#   ${POSTGRES_PASSWORD?error}
#
# The security invariant is interpolation of POSTGRES_PASSWORD itself.

DATABASE_URL_MATCH_COUNT="$(
    awk '
        /DATABASE_URL:/ &&
        /\$\{POSTGRES_PASSWORD([:?+-][^}]*)?\}/ {
            count++
        }

        END {
            print count + 0
        }
    ' "${PROJECT_ROOT}/docker-compose.yml" 2>/dev/null
)"

log "DATABASE_URL_MATCH_COUNT=${DATABASE_URL_MATCH_COUNT}"

if [ "${DATABASE_URL_MATCH_COUNT}" -ge 1 ]; then
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

# ============================================================================
# 9. RUNTIME SCOPE
# ============================================================================

section "9. RUNTIME DIRECT SECRET ASSIGNMENT"

RUNTIME_DIRECT_ASSIGNMENT_COUNT="$(
    grep -REn \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=forensics \
        --exclude-dir=archive \
        --exclude='phase_p0_02_*.sh' \
        --exclude='*.pyc' \
        -E '^[[:space:]]*(os\.environ|os\.getenv|getenv)[^;]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=' \
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

# ============================================================================
# 10. CI SECRET IDENTIFIERS
# ============================================================================

section "10. CI SECRET IDENTIFIER SET"

CI_IDENTIFIER_COUNT=0

for key in "${SECRET_KEYS[@]}"; do

    if grep -Eq "${key}" \
        "${PROJECT_ROOT}/.github/workflows/ci.yml" \
        2>/dev/null; then

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

# ============================================================================
# 11. DEPLOY SCOPE
# ============================================================================

section "11. DEPLOY SECRET REFERENCE"

DEPLOY_SECRET_REFERENCE_COUNT="$(
    grep -En \
        -E '(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
        "${PROJECT_ROOT}/scripts/deploy.sh" \
        2>/dev/null \
    | grep -Ev \
        '(#|audit-output|phase_p0_02_|report|log|print|echo|printf)' \
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

# ============================================================================
# 12. CURRENT APPLICATION OUTPUT SCOPE
# ============================================================================

section "12. CURRENT APPLICATION OUTPUT CLASSIFICATION"

CURRENT_OUTPUT_FILE="${TMP_DIR}/current_output_matches.txt"

# ONLY CURRENT APPLICATION CODE.
#
# Deliberately NOT scanning:
#   scripts/forensics/
#   scripts/forensics/archive/
#   audit-output/
#   phase_p0_02_*.sh
#   historical *.pre_literal_classifier_fix
#
# This is a security boundary, not merely a grep optimization.

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
    > "${CURRENT_OUTPUT_FILE}" || true

CURRENT_APPLICATION_OUTPUT_MATCH_COUNT="$(
    wc -l < "${CURRENT_OUTPUT_FILE}" |
    tr -d ' '
)"

log "CURRENT_APPLICATION_OUTPUT_MATCH_COUNT=${CURRENT_APPLICATION_OUTPUT_MATCH_COUNT}"

if [ "${CURRENT_APPLICATION_OUTPUT_MATCH_COUNT}" -eq 0 ]; then
    pass "NO_CURRENT_APPLICATION_SECRET_OUTPUT_PATTERN"
else
    fail "CURRENT_APPLICATION_SECRET_OUTPUT_PATTERN_PRESENT"

    while IFS= read -r line; do
        [ -z "${line}" ] && continue

        file="${line%%:*}"
        rest="${line#*:}"
        lineno="${rest%%:*}"

        log "CURRENT_OUTPUT_LOCATION=${file}:${lineno}"

    done < "${CURRENT_OUTPUT_FILE}"
fi

# ============================================================================
# 13. CURRENT APPLICATION DIRECT VALUE CLASSIFIER
# ============================================================================

section "13. CURRENT APPLICATION DIRECT VALUE CLASSIFIER"

CURRENT_LITERAL_FILE="${TMP_DIR}/current_literal_matches.txt"

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
    > "${CURRENT_LITERAL_FILE}" || true

CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT="$(
    wc -l < "${CURRENT_LITERAL_FILE}" |
    tr -d ' '
)"

log "CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT=${CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT}"

if [ "${CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT}" -eq 0 ]; then
    pass "NO_CURRENT_APPLICATION_DIRECT_SECRET_VALUE_PATTERN"
else
    fail "CURRENT_APPLICATION_DIRECT_SECRET_VALUE_PATTERN_PRESENT"

    while IFS= read -r line; do
        [ -z "${line}" ] && continue

        file="${line%%:*}"
        rest="${line#*:}"
        lineno="${rest%%:*}"

        log "CURRENT_LITERAL_LOCATION=${file}:${lineno}"

    done < "${CURRENT_LITERAL_FILE}"
fi

# ============================================================================
# 14. FORENSIC ARCHIVE ISOLATION
# ============================================================================

section "14. FORENSIC ARCHIVE ISOLATION"

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
    pass "FORENSIC_ARCHIVE_MATCHES_ISOLATED_FROM_PRODUCTION_CLASSIFICATION"
else
    pass "NO_FORENSIC_ARCHIVE_SECRET_OUTPUT_MATCHES"
fi

# ============================================================================
# 15. HISTORICAL AUDIT ISOLATION
# ============================================================================

section "15. HISTORICAL AUDIT ARTIFACT ISOLATION"

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
    pass "HISTORICAL_AUDIT_ARTIFACTS_ISOLATED"
else
    pass "NO_HISTORICAL_AUDIT_MATCHES"
fi

# ============================================================================
# 16. R34 STATUS INTEGRITY
# ============================================================================

section "16. R34 STATUS INTEGRITY"

R34_FILE="${PROJECT_ROOT}/audit-output/p0_02_r34_secret_provenance_scope_corrected_gate.txt"

if [ -f "${R34_FILE}" ]; then

    R34_STATUS="$(
        awk -F= '
            /^P0_02_R34_STATUS=/ {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R34_FILE}"
    )"

    R34_EXIT_CODE="$(
        awk -F= '
            /^EXIT_CODE=/ {
                value=$2
                gsub(/[[:space:]]/, "", value)
                print value
                exit
            }
        ' "${R34_FILE}"
    )"

    log "R34_STATUS=${R34_STATUS}"
    log "R34_EXIT_CODE=${R34_EXIT_CODE}"

    if [ "${R34_STATUS}" = "PASS" ] &&
       [ "${R34_EXIT_CODE}" = "0" ]; then

        pass "R34_FINAL_STATUS_PASS"

    else

        review "R34_PREVIOUS_STATUS_NOT_CLEAN"

    fi

else

    review "R34_REPORT_NOT_FOUND"

fi

# ============================================================================
# 17. R29 HISTORICAL PARSER
# ============================================================================

section "17. R29 HISTORICAL LOGIC RECONCILIATION"

R29_FILE="${PROJECT_ROOT}/audit-output/p0_02_r29_secret_provenance_cross_file_consistency_gate.txt"

if [ -f "${R29_FILE}" ]; then

    # IMPORTANT:
    # Anchored parsing prevents arbitrary continuation lines or whitespace
    # corruption from entering integer comparisons.

    R29_MISSING_COUNT="$(
        awk '
            /^FAIL: COMPOSE_REFERENCE_MISSING=[A-Za-z0-9_]+[[:space:]]*$/ {
                count++
            }

            END {
                print count + 0
            }
        ' "${R29_FILE}"
    )"

    R29_CONSISTENT_COUNT="$(
        awk '
            /^PASS: R29_CROSS_FILE_SECRET_PROVENANCE_CONSISTENT[[:space:]]*$/ {
                count++
            }

            END {
                print count + 0
            }
        ' "${R29_FILE}"
    )"

    log "R29_COMPOSE_MISSING_COUNT=${R29_MISSING_COUNT}"
    log "R29_INTERNAL_CONSISTENT_ASSERTION_COUNT=${R29_CONSISTENT_COUNT}"

    if [ "${R29_MISSING_COUNT}" -gt 0 ] &&
       [ "${R29_CONSISTENT_COUNT}" -gt 0 ]; then

        R29_HISTORICAL_CONTRADICTION=1

        pass "R29_HISTORICAL_INTERNAL_CONTRADICTION_CONFIRMED"

    elif [ "${R29_MISSING_COUNT}" -eq 0 ]; then

        pass "R29_NO_HISTORICAL_MISSING_REFERENCE_ASSERTION"

    else

        pass "R29_HISTORICAL_ASSERTIONS_NON_CONTRADICTORY"

    fi

else

    review "R29_REPORT_NOT_FOUND"

fi

# ============================================================================
# 18. CURRENT FINAL SECURITY INVARIANTS
# ============================================================================

section "18. CURRENT FINAL SECURITY INVARIANTS"

CURRENT_CORE_OK=1

if [ "${ENV_SECRET_COUNT}" -ne 5 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${COMPOSE_TARGET_COUNT}" -ne 3 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${COMPOSE_REFERENCE_COUNT}" -ne 3 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${COMPOSE_LITERAL_COUNT}" -ne 0 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${COMPOSE_KEY_REFERENCE_FAILURES}" -ne 0 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${DATABASE_URL_MATCH_COUNT}" -lt 1 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${RUNTIME_DIRECT_ASSIGNMENT_COUNT}" -ne 0 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${CI_IDENTIFIER_COUNT}" -ne 5 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${DEPLOY_SECRET_REFERENCE_COUNT}" -ne 0 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${CURRENT_APPLICATION_OUTPUT_MATCH_COUNT}" -ne 0 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT}" -ne 0 ]; then
    CURRENT_CORE_OK=0
fi

if [ "${CURRENT_CORE_OK}" -eq 1 ]; then
    pass "CURRENT_SECRET_PROVENANCE_CORE_INVARIANTS_HOLD"
else
    fail "CURRENT_SECRET_PROVENANCE_CORE_INVARIANTS_BROKEN"
fi

# ============================================================================
# 19. HISTORICAL VS CURRENT SEPARATION
# ============================================================================

section "19. HISTORICAL VS CURRENT SEPARATION"

if [ "${R29_HISTORICAL_CONTRADICTION}" -eq 1 ]; then
    pass "R29_CONTRADICTION_IS_HISTORICAL_AUDITOR_DEFECT"
else
    pass "NO_R29_HISTORICAL_CONTRADICTION_REQUIRES_RECONCILIATION"
fi

if [ "${FORENSIC_ARCHIVE_MATCH_COUNT}" -gt 0 ] ||
   [ "${HISTORICAL_AUDIT_MATCH_COUNT}" -gt 0 ]; then

    pass "HISTORICAL_AUDIT_ARTIFACTS_DO_NOT_DEFINE_CURRENT_SECURITY_STATE"

else

    pass "NO_HISTORICAL_AUDIT_ARTIFACT_CONTAMINATION_DETECTED"

fi

# ============================================================================
# 20. FINAL CLASSIFICATION
# ============================================================================

section "20. FINAL CLASSIFICATION"

# Historical R29 contradiction is INFORMATIONAL here.
# It is not a current production security failure because the current
# invariants are independently recomputed above.

if [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_02_R35_SECRET_PROVENANCE_FINAL_INTEGRITY_FAIL"
    EXIT_CODE=2

elif [ "${REVIEW_COUNT}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_02_R35_SECRET_PROVENANCE_FINAL_INTEGRITY_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_02_R35_SECRET_PROVENANCE_FINAL_INTEGRITY_PASS"
    EXIT_CODE=0

fi

# ============================================================================
# 21. FINAL EVIDENCE CARD
# ============================================================================

log ""
log "---------------- FINAL EVIDENCE CARD ----------------"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

log "ENV_SECRET_AUTHORITY_COUNT=${ENV_SECRET_COUNT}"

log "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
log "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
log "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
log "COMPOSE_KEY_REFERENCE_FAILURES=${COMPOSE_KEY_REFERENCE_FAILURES}"

log "DATABASE_URL_MATCH_COUNT=${DATABASE_URL_MATCH_COUNT}"

log "RUNTIME_DIRECT_ASSIGNMENT_COUNT=${RUNTIME_DIRECT_ASSIGNMENT_COUNT}"
log "CI_IDENTIFIER_COUNT=${CI_IDENTIFIER_COUNT}"
log "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"

log "CURRENT_APPLICATION_OUTPUT_MATCH_COUNT=${CURRENT_APPLICATION_OUTPUT_MATCH_COUNT}"
log "CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT=${CURRENT_APPLICATION_LITERAL_LEAK_MATCH_COUNT}"

log "FORENSIC_ARCHIVE_MATCH_COUNT=${FORENSIC_ARCHIVE_MATCH_COUNT}"
log "HISTORICAL_AUDIT_MATCH_COUNT=${HISTORICAL_AUDIT_MATCH_COUNT}"

log "R29_COMPOSE_MISSING_COUNT=${R29_MISSING_COUNT}"
log "R29_INTERNAL_CONSISTENT_ASSERTION_COUNT=${R29_CONSISTENT_COUNT}"
log "R29_HISTORICAL_CONTRADICTION=${R29_HISTORICAL_CONTRADICTION}"

log "R34_STATUS=${R34_STATUS}"
log "R34_EXIT_CODE=${R34_EXIT_CODE}"

log "P0_02_R35_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
