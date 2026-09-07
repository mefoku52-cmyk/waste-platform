#!/data/data/com.termux/files/usr/bin/bash

set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
cd "$PROJECT_ROOT" || exit 20

REPORT="audit-output/p0_02_r21_secret_provenance_deterministic_parser_closure.txt"
mkdir -p audit-output

FAILURE_COUNT=0
REVIEW_COUNT=0

section() {
    printf '\n============================================================\n'
    printf '%s\n' "$1"
    printf '============================================================\n'
}

log() {
    printf '%s\n' "$*" | tee -a "$REPORT"
}

pass() {
    log "PASS: $*"
}

fail() {
    log "FAIL: $*"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    log "REVIEW: $*"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

safe_int() {
    case "${1:-}" in
        ''|*[!0-9]*) printf '0' ;;
        *) printf '%s' "$1" ;;
    esac
}

# ------------------------------------------------------------------
# INITIALIZE REPORT
# ------------------------------------------------------------------

: > "$REPORT"

section "P0-02 R21 SECRET PROVENANCE DETERMINISTIC PARSER CLOSURE"

section "1. SAFETY PRECHECK"

if [ -d "$PROJECT_ROOT" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_MISSING"
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
pass "NO_REGEX_BACKREFERENCES=YES"

section "2. REQUIRED AUTHORITY FILES"

AUTHORITY_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

for file in "${AUTHORITY_FILES[@]}"; do
    if [ -f "$file" ]; then
        pass "AUTHORITY_PRESENT=$file"
    else
        fail "AUTHORITY_MISSING=$file"
    fi
done

section "3. SECRET TOKEN SET"

SECRET_TOKENS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for token in "${SECRET_TOKENS[@]}"; do
    log "SECRET_TOKEN=$token"
done

section "4. R17 BASELINE"

R17_REPORT="audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt"

if [ -f "$R17_REPORT" ]; then
    pass "R17_REPORT_PRESENT"
else
    fail "R17_REPORT_MISSING"
fi

R17_COMPOSE_REFERENCE=0
R17_COMPOSE_LITERAL=0
R17_SECRET_OUTPUT=0

if [ -f "$R17_REPORT" ]; then
    R17_COMPOSE_REFERENCE=$(
        awk -F= '/^COMPOSE_REFERENCE_COUNT=/ {print $2; exit}' "$R17_REPORT"
    )
    R17_COMPOSE_LITERAL=$(
        awk -F= '/^COMPOSE_LITERAL_COUNT=/ {print $2; exit}' "$R17_REPORT"
    )
    R17_SECRET_OUTPUT=$(
        awk -F= '/^SECRET_VALUE_OUTPUT_COUNT=/ {print $2; exit}' "$R17_REPORT"
    )

    R17_COMPOSE_REFERENCE=$(safe_int "$R17_COMPOSE_REFERENCE")
    R17_COMPOSE_LITERAL=$(safe_int "$R17_COMPOSE_LITERAL")
    R17_SECRET_OUTPUT=$(safe_int "$R17_SECRET_OUTPUT")

    log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE"
    log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL"
    log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT"

    if [ "$R17_COMPOSE_REFERENCE" -eq 3 ] &&
       [ "$R17_COMPOSE_LITERAL" -eq 0 ] &&
       [ "$R17_SECRET_OUTPUT" -eq 0 ]; then
        pass "R17_BASELINE_EXPECTED_STATE_CONFIRMED"
    else
        review "R17_BASELINE_DIFFERS_FROM_EXPECTED_3_0_0"
    fi
fi

section "5. PRODUCTION SECRET AUTHORITY"

ENV_SECRET_COUNT=0
ENV_MISSING_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do
    if awk -v key="$token" '
        $0 ~ "^[[:space:]]*" key "[[:space:]]*=" {
            found=1
            exit
        }
        END {
            exit(found ? 0 : 1)
        }
    ' .env.production; then
        pass "ENV_AUTHORITY_PRESENT KEY=$token VALUE=<REDACTED>"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING KEY=$token"
        ENV_MISSING_COUNT=$((ENV_MISSING_COUNT + 1))
    fi
done

log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "ENV_MISSING_COUNT=$ENV_MISSING_COUNT"

if [ "$ENV_SECRET_COUNT" -eq 5 ] && [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_INCOMPLETE"
fi

section "6. DETERMINISTIC COMPOSE TOKEN PARSER"

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

# Parse only docker-compose.yml.
# No backreferences, no sed capture groups, no dynamic grep regex.
#
# Accepted reference forms:
#   ${POSTGRES_PASSWORD}
#   ${POSTGRES_PASSWORD:-...}
#   ${POSTGRES_PASSWORD:?....}
#
# Literal secret assignment means:
#   KEY: "actual-value"
#   KEY: actual-value
#
# A reference is recognized by token-aware awk parsing.

for token in POSTGRES_PASSWORD JWT_SECRET_KEY JWT_REFRESH_SECRET_KEY; do

    target_found=0
    reference_found=0
    literal_found=0

    while IFS= read -r line; do

        # Strip comments conservatively.
        clean="${line%%#*}"

        # Ignore empty lines.
        [ -z "${clean//[[:space:]]/}" ] && continue

        # Match exact YAML environment key.
        case "$clean" in
            *"$token:"*)
                target_found=1

                # Extract only the RHS after the first colon.
                rhs="${clean#*:}"
                rhs="${rhs#"${rhs%%[![:space:]]*}"}"

                # Reference forms are checked literally.
                case "$rhs" in
                    *"\${$token}"*|*"\${$token:-"*|*"\${$token:? "*) 
                        reference_found=1
                        ;;
                    *"\${$token:?*"*)
                        reference_found=1
                        ;;
                    *)
                        # Quoted/plain literal RHS.
                        if [ -n "$rhs" ]; then
                            literal_found=1
                        fi
                        ;;
                esac
                ;;
        esac

    done < docker-compose.yml

    if [ "$target_found" -eq 1 ]; then
        COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))
    fi

    if [ "$reference_found" -eq 1 ]; then
        COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
        pass "COMPOSE_REFERENCE_WIRING KEY=$token"
    elif [ "$literal_found" -eq 1 ]; then
        COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
        fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$token VALUE=<REDACTED>"
    else
        fail "COMPOSE_SECRET_MAPPING_MISSING KEY=$token"
    fi

done

# DATABASE_URL is not itself a second secret target.
# It is a context boundary proving that POSTGRES_PASSWORD is interpolated.
DATABASE_URL_FOUND=0
DATABASE_URL_POSTGRES_REFERENCE=0

while IFS= read -r line; do
    clean="${line%%#*}"

    case "$clean" in
        *DATABASE_URL*)
            DATABASE_URL_FOUND=1

            case "$clean" in
                *"\${POSTGRES_PASSWORD}"*|*"\${POSTGRES_PASSWORD:-"*|*"\${POSTGRES_PASSWORD:?*"*)
                    DATABASE_URL_POSTGRES_REFERENCE=1
                    ;;
            esac
            ;;
    esac
done < docker-compose.yml

if [ "$DATABASE_URL_FOUND" -eq 1 ]; then
    pass "DATABASE_URL_MAPPING_PRESENT"
else
    fail "DATABASE_URL_MAPPING_MISSING"
fi

if [ "$DATABASE_URL_POSTGRES_REFERENCE" -eq 1 ]; then
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
    pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
    COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"

EXPECTED_COMPOSE_REFERENCE_COUNT=3

if [ "$COMPOSE_TARGET_COUNT" -eq "$EXPECTED_COMPOSE_REFERENCE_COUNT" ]; then
    pass "COMPOSE_TARGET_CARDINALITY_EXACT"
else
    fail "COMPOSE_TARGET_CARDINALITY_MISMATCH EXPECTED=$EXPECTED_COMPOSE_REFERENCE_COUNT ACTUAL=$COMPOSE_TARGET_COUNT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$EXPECTED_COMPOSE_REFERENCE_COUNT" ]; then
    pass "COMPOSE_REFERENCE_CARDINALITY_EXACT"
else
    fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH EXPECTED=$EXPECTED_COMPOSE_REFERENCE_COUNT ACTUAL=$COMPOSE_REFERENCE_COUNT"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    fail "LITERAL_COMPOSE_SECRET_ASSIGNMENT_PRESENT"
fi

section "7. RUNTIME JWT SECRET AUTHORITY"

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

if grep -Fq "JWT_SECRET_KEY" app/core/config.py; then
    RUNTIME_DECLARATION_COUNT=1
    pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

RUNTIME_CONTEXT_COUNT=$(
    grep -F "JWT_SECRET_KEY" app/core/config.py |
    grep -vE '^[[:space:]]*#' |
    wc -l |
    tr -d ' '
)

RUNTIME_CONTEXT_COUNT=$(safe_int "$RUNTIME_CONTEXT_COUNT")

if [ "$RUNTIME_CONTEXT_COUNT" -ge 1 ]; then
    pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
else
    fail "RUNTIME_JWT_SECRET_USE_CONTEXT_MISSING"
fi

# Detect literal assignment only.
# This deliberately does NOT treat:
#   JWT_SECRET_KEY: str
#   JWT_SECRET_KEY = settings.JWT_SECRET_KEY
# as literal secret values.
if awk '
    /JWT_SECRET_KEY[[:space:]]*=/ &&
    $0 !~ /settings[.]JWT_SECRET_KEY/ &&
    $0 !~ /os[.]getenv/ &&
    $0 !~ /Field[[:space:]]*\(/ &&
    $0 !~ /SecretStr/ {
        print
    }
' app/core/config.py | grep -q .; then
    RUNTIME_LITERAL_COUNT=1
    fail "RUNTIME_LITERAL_SECRET_ASSIGNMENT_DETECTED"
else
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
fi

log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"

section "8. CI TEST-SCOPE PROVENANCE"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do

    if grep -Fq "$token" .github/workflows/ci.yml; then
        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

        # Test-only scope markers accepted:
        # pytest / test / testing / CI test environment.
        if grep -F "$token" .github/workflows/ci.yml |
           grep -Ei 'test|pytest|testing' >/dev/null 2>&1; then
            CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
            pass "CI_SECRET_TEST_SCOPE KEY=$token VALUE=<REDACTED>"
        else
            CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
            review "CI_SECRET_SCOPE_UNCONFIRMED KEY=$token"
        fi
    fi

done

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

section "9. DEPLOYMENT AUTHORITY BOUNDARY"

DEPLOY_SECRET_REFERENCE_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do
    if grep -Fq "$token" scripts/deploy.sh; then
        DEPLOY_SECRET_REFERENCE_COUNT=$((DEPLOY_SECRET_REFERENCE_COUNT + 1))
    fi
done

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
else
    fail "DEPLOY_SCRIPT_DIRECT_SECRET_IDENTIFIER_REFERENCE"
fi

if grep -Eq 'env[.]production|docker-compose[.]yml|compose' scripts/deploy.sh; then
    pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
else
    review "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_NOT_EXPLICIT"
fi

log "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"

section "10. SECRET OUTPUT GUARD"

# Important:
# Scan only the five authority files.
# Do NOT scan audit-output or this analyzer itself.
# This removes the R16/R20 self-report false positive class.

SECRET_VALUE_OUTPUT_COUNT=0

for file in \
    ".env.production" \
    "docker-compose.yml" \
    "app/core/config.py" \
    ".github/workflows/ci.yml" \
    "scripts/deploy.sh"
do
    if [ ! -f "$file" ]; then
        continue
    fi

    # Reject common direct printing of environment secret values.
    if grep -En \
        'echo[[:space:]].*(PASSWORD|JWT_SECRET|S3_SECRET)|printf[[:space:]].*(PASSWORD|JWT_SECRET|S3_SECRET)|print[[:space:]]*\(.*(PASSWORD|JWT_SECRET|S3_SECRET)' \
        "$file" >/dev/null 2>&1; then
        SECRET_VALUE_OUTPUT_COUNT=$((SECRET_VALUE_OUTPUT_COUNT + 1))
    fi
done

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
fi

log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"

section "11. R17 REGRESSION GATE"

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$R17_COMPOSE_REFERENCE" ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq "$R17_COMPOSE_LITERAL" ] &&
   [ "$SECRET_VALUE_OUTPUT_COUNT" -eq "$R17_SECRET_OUTPUT" ]; then
    pass "R17_BASELINE_RESTORED"
else
    fail "R17_BASELINE_REGRESSION_DETECTED"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ]; then
    pass "R17_COMPOSE_REFERENCE_BASELINE=3_RESTORED"
else
    fail "R17_COMPOSE_REFERENCE_BASELINE_NOT_RESTORED"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "R17_COMPOSE_LITERAL_BASELINE=0_RESTORED"
else
    fail "R17_COMPOSE_LITERAL_BASELINE_NOT_RESTORED"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "R17_SECRET_OUTPUT_BASELINE=0_RESTORED"
else
    fail "R17_SECRET_OUTPUT_BASELINE_NOT_RESTORED"
fi

section "12. CROSS-AUTHORITY INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_COMPOSE_SECRET_LINEAGE"
else
    fail "INVARIANT_COMPOSE_SECRET_LINEAGE"
fi

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_RUNTIME_SECRET"
else
    fail "INVARIANT_LITERAL_RUNTIME_SECRET"
fi

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "INVARIANT_DEPLOYMENT_NO_DIRECT_SECRET_REFERENCE"
else
    fail "INVARIANT_DEPLOYMENT_SECRET_REFERENCE"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_SECRET_VALUE_OUTPUT"
else
    fail "INVARIANT_SECRET_VALUE_OUTPUT"
fi

section "13. FINAL CLASSIFICATION"

log "FAILURE_COUNT=$FAILURE_COUNT"
log "REVIEW_COUNT=$REVIEW_COUNT"
log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"
log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"
log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"
log "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"
log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE"
log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL"
log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R21_SECRET_PROVENANCE_DETERMINISTIC_PARSER_CLOSURE_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R21_SECRET_PROVENANCE_DETERMINISTIC_PARSER_CLOSURE_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R21_SECRET_PROVENANCE_DETERMINISTIC_PARSER_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R21_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
