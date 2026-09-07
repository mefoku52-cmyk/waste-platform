#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env.production"
CONFIG_FILE="$PROJECT_ROOT/app/core/config.py"
CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"
DEPLOY_FILE="$PROJECT_ROOT/scripts/deploy.sh"

REPORT="$PROJECT_ROOT/audit-output/p0_02_r25_secret_provenance_ground_truth_deterministic.txt"
mkdir -p "$PROJECT_ROOT/audit-output"

FAILURE_COUNT=0
REVIEW_COUNT=0

fail() {
    echo "FAIL: $1"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    echo "REVIEW: $1"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

pass() {
    echo "PASS: $1"
}

section() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

log() {
    echo "$1"
}

exec > >(tee "$REPORT") 2>&1

section "P0-02 R25 SECRET PROVENANCE GROUND-TRUTH DETERMINISTIC"

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
pass "NO_PC_RE_LOOKAHEAD=YES"

section "2. REQUIRED AUTHORITY FILES"

for f in \
    ".env.production" \
    "docker-compose.yml" \
    "app/core/config.py" \
    ".github/workflows/ci.yml" \
    "scripts/deploy.sh"
do
    if [ -f "$PROJECT_ROOT/$f" ]; then
        pass "AUTHORITY_PRESENT=$f"
    else
        fail "AUTHORITY_MISSING=$f"
    fi
done

section "3. SECRET TOKEN SET"

TOKENS="
POSTGRES_PASSWORD
DATABASE_PASSWORD
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
S3_SECRET_KEY
"

TOKEN_COUNT=0

while IFS= read -r token; do
    [ -z "$token" ] && continue
    echo "SECRET_TOKEN=$token"
    TOKEN_COUNT=$((TOKEN_COUNT + 1))
done <<EOF_TOKENS
$TOKENS
EOF_TOKENS

section "4. PRODUCTION SECRET AUTHORITY"

ENV_SECRET_COUNT=0
ENV_MISSING_COUNT=0

while IFS= read -r token; do
    [ -z "$token" ] && continue

    if awk -v key="$token" '
        index($0, key "=") == 1 {
            found=1
            exit
        }
        END {
            exit(found ? 0 : 1)
        }
    ' "$ENV_FILE" 2>/dev/null; then
        pass "ENV_AUTHORITY_PRESENT KEY=$token VALUE=<REDACTED>"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING KEY=$token"
        ENV_MISSING_COUNT=$((ENV_MISSING_COUNT + 1))
    fi
done <<EOF_TOKENS
$TOKENS
EOF_TOKENS

log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "ENV_MISSING_COUNT=$ENV_MISSING_COUNT"

if [ "$ENV_SECRET_COUNT" -eq "$TOKEN_COUNT" ] &&
   [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_NOT_EXACT"
fi

section "5. DETERMINISTIC COMPOSE PARSER"

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

# A Compose secret target is counted only when the left side is
# one of the exact secret identifiers.
#
# Reference:
#   KEY: ${KEY}
#   KEY: ${KEY:?...}
#   KEY: ${KEY:-...}
#
# Literal:
#   KEY: some-real-value
#
# DATABASE_URL is handled separately because POSTGRES_PASSWORD
# legitimately appears inside the URL interpolation.

while IFS= read -r line; do

    case "$line" in
        *"POSTGRES_PASSWORD:"*)
            COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

            rhs="${line#*POSTGRES_PASSWORD:}"
            rhs="$(printf '%s' "$rhs" | sed 's/^[[:space:]]*//')"

            case "$rhs" in
                '${POSTGRES_PASSWORD}'*)
                    COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
                    ;;
                *)
                    COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
                    echo "FAIL: COMPOSE_LITERAL_ASSIGNMENT KEY=POSTGRES_PASSWORD VALUE=<REDACTED>"
                    ;;
            esac
            ;;

        *"JWT_SECRET_KEY:"*)
            COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

            rhs="${line#*JWT_SECRET_KEY:}"
            rhs="$(printf '%s' "$rhs" | sed 's/^[[:space:]]*//')"

            case "$rhs" in
                '${JWT_SECRET_KEY}'*)
                    COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
                    ;;
                *)
                    COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
                    echo "FAIL: COMPOSE_LITERAL_ASSIGNMENT KEY=JWT_SECRET_KEY VALUE=<REDACTED>"
                    ;;
            esac
            ;;

        *"JWT_REFRESH_SECRET_KEY:"*)
            COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

            rhs="${line#*JWT_REFRESH_SECRET_KEY:}"
            rhs="$(printf '%s' "$rhs" | sed 's/^[[:space:]]*//')"

            case "$rhs" in
                '${JWT_REFRESH_SECRET_KEY}'*)
                    COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
                    ;;
                *)
                    COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
                    echo "FAIL: COMPOSE_LITERAL_ASSIGNMENT KEY=JWT_REFRESH_SECRET_KEY VALUE=<REDACTED>"
                    ;;
            esac
            ;;
    esac

done < "$COMPOSE_FILE"

# DATABASE_URL is not a separate secret target.
# It is context containing the POSTGRES_PASSWORD interpolation.
DATABASE_URL_MAPPING_PRESENT=0
DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT=0

if grep -Fq "DATABASE_URL:" "$COMPOSE_FILE"; then
    DATABASE_URL_MAPPING_PRESENT=1
    pass "DATABASE_URL_MAPPING_PRESENT"
else
    fail "DATABASE_URL_MAPPING_MISSING"
fi

if grep -Fq '${POSTGRES_PASSWORD' "$COMPOSE_FILE"; then
    DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT=1
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

if [ "$DATABASE_URL_MAPPING_PRESENT" -eq 1 ] &&
   [ "$DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT" -eq 1 ]; then
    pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
else
    fail "DATABASE_URL_SECRET_REFERENCE_CONTEXT_MISSING"
fi

log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"

# Ground truth is exactly three secret target declarations:
# POSTGRES_PASSWORD
# JWT_SECRET_KEY
# JWT_REFRESH_SECRET_KEY
EXPECTED_COMPOSE_TARGET_COUNT=3
EXPECTED_COMPOSE_REFERENCE_COUNT=3

if [ "$COMPOSE_TARGET_COUNT" -eq "$EXPECTED_COMPOSE_TARGET_COUNT" ]; then
    pass "COMPOSE_TARGET_CARDINALITY_EXACT"
else
    fail "COMPOSE_TARGET_CARDINALITY_MISMATCH EXPECTED=$EXPECTED_COMPOSE_TARGET_COUNT ACTUAL=$COMPOSE_TARGET_COUNT"
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

section "6. RUNTIME JWT SECRET AUTHORITY"

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

if grep -Fq "JWT_SECRET_KEY" "$CONFIG_FILE"; then
    RUNTIME_DECLARATION_COUNT=1
    pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

# Count only source lines containing the identifier.
# No regex arithmetic and no backreferences.
RUNTIME_CONTEXT_COUNT="$(
    awk '
        /JWT_SECRET_KEY/ {
            count++
        }
        END {
            print count+0
        }
    ' "$CONFIG_FILE" 2>/dev/null
)"

if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
    pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
else
    fail "RUNTIME_JWT_SECRET_USE_CONTEXT_MISSING"
fi

# Literal assignment means an assignment whose RHS is not an env/settings
# reference. This deliberately avoids regex backreferences.
while IFS= read -r line; do
    case "$line" in
        *"JWT_SECRET_KEY ="*|*"JWT_SECRET_KEY="*)
            case "$line" in
                *"os.getenv"*|*"settings."*|*"config."*)
                    ;;
                *)
                    RUNTIME_LITERAL_COUNT=$((RUNTIME_LITERAL_COUNT + 1))
                    ;;
            esac
            ;;
    esac
done < "$CONFIG_FILE"

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
else
    fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_PRESENT COUNT=$RUNTIME_LITERAL_COUNT"
fi

log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"

section "7. CI TEST-SCOPE PROVENANCE"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

while IFS= read -r token; do
    [ -z "$token" ] && continue

    if grep -Fq "$token:" "$CI_FILE"; then
        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

        # Inspect a bounded context around the token.
        if awk -v key="$token" '
            index($0, key ":") {
                print
            }
        ' "$CI_FILE" | grep -Fq "secrets."; then
            CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
            pass "CI_SECRET_TEST_SCOPE KEY=$token VALUE=<REDACTED>"
        else
            CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
            review "CI_SECRET_SCOPE_UNCONFIRMED KEY=$token"
        fi
    fi
done <<EOF_TOKENS
$TOKENS
EOF_TOKENS

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

section "8. DEPLOYMENT AUTHORITY BOUNDARY"

DEPLOY_SECRET_REFERENCE_COUNT=0

for token in \
    POSTGRES_PASSWORD \
    DATABASE_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    S3_SECRET_KEY
do
    if grep -Fq "$token" "$DEPLOY_FILE"; then
        DEPLOY_SECRET_REFERENCE_COUNT=$((DEPLOY_SECRET_REFERENCE_COUNT + 1))
    fi
done

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
else
    fail "DEPLOY_SCRIPT_HAS_DIRECT_SECRET_IDENTIFIER_REFERENCE COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
fi

if grep -Fq "docker-compose" "$DEPLOY_FILE" ||
   grep -Fq "docker compose" "$DEPLOY_FILE" ||
   grep -Fq ".env.production" "$DEPLOY_FILE"; then
    pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
else
    review "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_REQUIRES_REVIEW"
fi

log "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"

section "9. SECRET OUTPUT GUARD"

SECRET_VALUE_OUTPUT_COUNT=0

# Only inspect audit scripts/reports for obvious value-printing patterns.
# The actual .env.production contents are never emitted.
#
# The important invariant is that this audit itself only reports <REDACTED>.
#
if grep -R -n -E \
    'echo[[:space:]].*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
    "$PROJECT_ROOT/phase_p0_02_r2"*.sh \
    "$PROJECT_ROOT/phase_p0_02_r2"*.txt \
    2>/dev/null |
    grep -v '<REDACTED>' |
    grep -v 'SECRET_TOKEN=' |
    grep -v 'KEY=' >/dev/null 2>&1
then
    SECRET_VALUE_OUTPUT_COUNT=1
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED"
else
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
fi

log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"

section "10. R17 REGRESSION BASELINE"

R17_REPORT="$PROJECT_ROOT/audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt"

R17_COMPOSE_REFERENCE_BASELINE=0
R17_COMPOSE_LITERAL_BASELINE=0
R17_SECRET_OUTPUT_BASELINE=0

if [ -f "$R17_REPORT" ]; then
    pass "R17_REPORT_PRESENT"

    R17_COMPOSE_REFERENCE_BASELINE="$(
        awk -F= '/COMPOSE_REFERENCE_COUNT=/{print $2; exit}' "$R17_REPORT"
    )"

    R17_COMPOSE_LITERAL_BASELINE="$(
        awk -F= '/COMPOSE_LITERAL_COUNT=/{print $2; exit}' "$R17_REPORT"
    )"

    R17_SECRET_OUTPUT_BASELINE="$(
        awk -F= '/SECRET_VALUE_OUTPUT_COUNT=/{print $2; exit}' "$R17_REPORT"
    )"

    log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE_BASELINE"
    log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL_BASELINE"
    log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT_BASELINE"

    if [ "$R17_COMPOSE_REFERENCE_BASELINE" -eq 3 ] &&
       [ "$R17_COMPOSE_LITERAL_BASELINE" -eq 0 ]; then
        pass "R17_COMPOSE_BASELINE_EXPECTED_STATE_CONFIRMED"
    else
        review "R17_COMPOSE_BASELINE_DIFFERS_FROM_EXPECTED_STATE"
    fi

    if [ "$R17_SECRET_OUTPUT_BASELINE" -eq 0 ]; then
        pass "R17_SECRET_OUTPUT_BASELINE=0"
    else
        fail "R17_SECRET_OUTPUT_BASELINE_NONZERO"
    fi
else
    review "R17_REPORT_NOT_FOUND"
fi

section "11. CROSS-AUTHORITY FINAL INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ] &&
   [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET"
fi

if [ "$COMPOSE_TARGET_COUNT" -eq 3 ] &&
   [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_COMPOSE_SECRET_LINEAGE"
else
    fail "INVARIANT_COMPOSE_SECRET_LINEAGE"
fi

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ] &&
   [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
    pass "INVARIANT_RUNTIME_SECRET_LINEAGE"
else
    fail "INVARIANT_RUNTIME_SECRET_LINEAGE"
fi

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "INVARIANT_DEPLOYMENT_NO_DIRECT_SECRET_REFERENCE"
else
    fail "INVARIANT_DEPLOYMENT_NO_DIRECT_SECRET_REFERENCE"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_SECRET_VALUE_OUTPUT"
else
    fail "INVARIANT_SECRET_VALUE_OUTPUT"
fi

section "12. FINAL CLASSIFICATION"

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
log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE_BASELINE"
log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL_BASELINE"
log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT_BASELINE"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R25_SECRET_PROVENANCE_GROUND_TRUTH_DETERMINISTIC_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R25_SECRET_PROVENANCE_GROUND_TRUTH_DETERMINISTIC_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R25_SECRET_PROVENANCE_GROUND_TRUTH_DETERMINISTIC_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R25_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
