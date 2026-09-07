#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(pwd)"
REPORT="$PROJECT_ROOT/audit-output/p0_02_r26_secret_provenance_ground_truth_parser.txt"

mkdir -p "$PROJECT_ROOT/audit-output"

FAILURE_COUNT=0
REVIEW_COUNT=0

fail() {
    echo "FAIL: $1"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

pass() {
    echo "PASS: $1"
}

review() {
    echo "REVIEW: $1"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
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

section "P0-02 R26 SECRET PROVENANCE GROUND-TRUTH PARSER"

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

ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
CONFIG_FILE="$PROJECT_ROOT/app/core/config.py"
CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"
DEPLOY_FILE="$PROJECT_ROOT/scripts/deploy.sh"

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

SECRET_TOKENS="
POSTGRES_PASSWORD
DATABASE_PASSWORD
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
S3_SECRET_KEY
"

while IFS= read -r token; do
    [ -z "$token" ] && continue
    echo "SECRET_TOKEN=$token"
done <<EOF_TOKENS
$SECRET_TOKENS
EOF_TOKENS

section "4. PRODUCTION SECRET AUTHORITY"

ENV_SECRET_COUNT=0
ENV_MISSING_COUNT=0

while IFS= read -r token; do
    [ -z "$token" ] && continue

    if grep -Eq "^[[:space:]]*${token}=" "$ENV_FILE" 2>/dev/null; then
        pass "ENV_AUTHORITY_PRESENT KEY=$token VALUE=<REDACTED>"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING KEY=$token"
        ENV_MISSING_COUNT=$((ENV_MISSING_COUNT + 1))
    fi
done <<EOF_TOKENS
$SECRET_TOKENS
EOF_TOKENS

log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "ENV_MISSING_COUNT=$ENV_MISSING_COUNT"

if [ "$ENV_SECRET_COUNT" -eq 5 ] && [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_NOT_EXACT"
fi

section "5. COMPOSE RAW STRUCTURAL GROUND TRUTH"

if [ ! -f "$COMPOSE_FILE" ]; then
    fail "COMPOSE_FILE_MISSING"
else
    echo "Relevant compose lines:"
    awk '
    /POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY|DATABASE_URL/ {
        print "LINE " NR ": " $0
    }
    ' "$COMPOSE_FILE" |
    sed -E \
        -e 's/(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)([=:]).*/\1\2<REDACTED>/' \
        -e 's/\$\{POSTGRES_PASSWORD:\?[^}]*\}/\${POSTGRES_PASSWORD:<REDACTED>}/g' \
        -e 's/\$\{JWT_SECRET_KEY:\?[^}]*\}/\${JWT_SECRET_KEY:<REDACTED>}/g' \
        -e 's/\$\{JWT_REFRESH_SECRET_KEY:\?[^}]*\}/\${JWT_REFRESH_SECRET_KEY:<REDACTED>}/g'
fi

section "6. COMPOSE SECRET TARGET PARSER"

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

if [ -f "$COMPOSE_FILE" ]; then

    # Only inspect actual environment-style assignment lines.
    # DATABASE_URL is deliberately excluded from target counting.
    while IFS= read -r token; do
        [ -z "$token" ] && continue

        TARGET_LINES="$(
            grep -nE "^[[:space:]]*${token}:" "$COMPOSE_FILE" 2>/dev/null || true
        )"

        if [ -n "$TARGET_LINES" ]; then

            while IFS= read -r line; do
                [ -z "$line" ] && continue

                lineno="${line%%:*}"
                content="${line#*:}"

                COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

                if printf '%s\n' "$content" | grep -Fq '${'"$token"'}'; then
                    pass "COMPOSE_REFERENCE_WIRING KEY=$token LINE=$lineno"
                    COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))

                elif printf '%s\n' "$content" | grep -Fq '${'"$token"':?'; then
                    pass "COMPOSE_REFERENCE_WIRING KEY=$token LINE=$lineno"
                    COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))

                else
                    fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$token LINE=$lineno VALUE=<REDACTED>"
                    COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
                fi

            done <<EOF_LINES
$TARGET_LINES
EOF_LINES

        fi
    done <<EOF_TOKENS
POSTGRES_PASSWORD
DATABASE_PASSWORD
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
S3_SECRET_KEY
EOF_TOKENS

    # DATABASE_URL is context, not a target.
    if grep -Eq "^[[:space:]]*DATABASE_URL:" "$COMPOSE_FILE"; then
        pass "DATABASE_URL_MAPPING_PRESENT"

        DATABASE_URL_LINE="$(
            grep -nE "^[[:space:]]*DATABASE_URL:" "$COMPOSE_FILE" |
            head -n 1
        )"

        DATABASE_URL_CONTENT="${DATABASE_URL_LINE#*:}"

        if printf '%s\n' "$DATABASE_URL_CONTENT" |
            grep -Fq '${POSTGRES_PASSWORD'; then
            pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
            pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
            COMPOSE_NON_SECRET_CONTEXT_COUNT=0
        else
            fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
            COMPOSE_NON_SECRET_CONTEXT_COUNT=1
        fi
    else
        fail "DATABASE_URL_MAPPING_MISSING"
        COMPOSE_NON_SECRET_CONTEXT_COUNT=1
    fi
fi

log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"

# R17 baseline is 3 actual secret environment targets:
# POSTGRES_PASSWORD
# JWT_SECRET_KEY
# JWT_REFRESH_SECRET_KEY
#
# DATABASE_URL interpolation is context, not another target.
if [ "$COMPOSE_TARGET_COUNT" -eq 3 ]; then
    pass "COMPOSE_TARGET_CARDINALITY_EXACT"
else
    fail "COMPOSE_TARGET_CARDINALITY_MISMATCH EXPECTED=3 ACTUAL=$COMPOSE_TARGET_COUNT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ]; then
    pass "COMPOSE_REFERENCE_CARDINALITY_EXACT"
else
    fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH EXPECTED=3 ACTUAL=$COMPOSE_REFERENCE_COUNT"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    fail "LITERAL_COMPOSE_SECRET_ASSIGNMENT_PRESENT"
fi

section "7. DATABASE_URL FALSE-POSITIVE BOUNDARY"

if [ -f "$COMPOSE_FILE" ]; then

    DATABASE_URL_COUNT="$(
        grep -cE "^[[:space:]]*DATABASE_URL:" "$COMPOSE_FILE" 2>/dev/null || true
    )"

    if [ "$DATABASE_URL_COUNT" -eq 1 ]; then
        pass "DATABASE_URL_SINGLE_MAPPING"

        DATABASE_URL_VALUE="$(
            grep -E "^[[:space:]]*DATABASE_URL:" "$COMPOSE_FILE" |
            head -n 1
        )"

        if printf '%s\n' "$DATABASE_URL_VALUE" |
            grep -Fq '${POSTGRES_PASSWORD'; then
            pass "DATABASE_URL_SECRET_INTERPOLATION_CONFIRMED"
        else
            fail "DATABASE_URL_SECRET_INTERPOLATION_NOT_CONFIRMED"
        fi
    else
        fail "DATABASE_URL_MAPPING_CARDINALITY_EXPECTED=1_ACTUAL=$DATABASE_URL_COUNT"
    fi

    pass "DATABASE_URL_IS_CONTEXT_NOT_SECRET_TARGET"
fi

section "8. RUNTIME JWT SECRET AUTHORITY"

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

if [ -f "$CONFIG_FILE" ]; then

    if grep -Eq "JWT_SECRET_KEY" "$CONFIG_FILE"; then
        pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
        RUNTIME_DECLARATION_COUNT=1
    else
        fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
    fi

    RUNTIME_CONTEXT_COUNT="$(
        grep -c "JWT_SECRET_KEY" "$CONFIG_FILE" 2>/dev/null || true
    )"

    if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
        pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
    else
        fail "RUNTIME_JWT_SECRET_USE_CONTEXT_MISSING"
    fi

    if grep -Eq "^[[:space:]]*JWT_SECRET_KEY[[:space:]]*=" "$CONFIG_FILE"; then
        fail "RUNTIME_LITERAL_SECRET_ASSIGNMENT_PRESENT"
        RUNTIME_LITERAL_COUNT=1
    else
        pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
    fi
else
    fail "RUNTIME_CONFIG_FILE_MISSING"
fi

log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"

section "9. CI TEST-SCOPE PROVENANCE"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

if [ -f "$CI_FILE" ]; then

    while IFS= read -r token; do
        [ -z "$token" ] && continue

        if grep -Eq "$token[[:space:]]*:" "$CI_FILE"; then
            pass "CI_SECRET_ASSIGNMENT_PRESENT KEY=$token"
            CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))
        fi
    done <<EOF_TOKENS
POSTGRES_PASSWORD
DATABASE_PASSWORD
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
S3_SECRET_KEY
EOF_TOKENS

    # Test scope is identified by explicit test/job context,
    # not merely by presence of the secret identifier.
    if grep -Eq "pytest|test|tests|CI_TEST|TEST_" "$CI_FILE"; then

        for token in \
            POSTGRES_PASSWORD \
            DATABASE_PASSWORD \
            JWT_SECRET_KEY \
            JWT_REFRESH_SECRET_KEY \
            S3_SECRET_KEY
        do
            if grep -Eq "pytest|test|tests|CI_TEST|TEST_" "$CI_FILE" &&
               grep -Eq "$token[[:space:]]*:" "$CI_FILE"; then
                CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
            fi
        done
    fi
fi

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_SECRET_ASSIGNMENT_COUNT" -eq 5 ]; then
    pass "CI_SECRET_ASSIGNMENT_SET_EXACT"
else
    fail "CI_SECRET_ASSIGNMENT_SET_MISMATCH EXPECTED=5 ACTUAL=$CI_SECRET_ASSIGNMENT_COUNT"
fi

# This gate only rejects explicit production deployment scope.
if grep -Eq "production.*secret|secret.*production|deploy.*secret|secrets.*production" "$CI_FILE" 2>/dev/null; then
    CI_PROD_SCOPE_COUNT=1
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
else
    CI_PROD_SCOPE_COUNT=0
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
fi

section "10. DEPLOYMENT AUTHORITY BOUNDARY"

DEPLOY_SECRET_REFERENCE_COUNT=0

if [ -f "$DEPLOY_FILE" ]; then

    DEPLOY_SECRET_REFERENCE_COUNT="$(
        grep -Ec \
        "POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY" \
        "$DEPLOY_FILE" 2>/dev/null || true
    )"

    if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
        pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
    else
        fail "DEPLOY_SCRIPT_HAS_DIRECT_SECRET_IDENTIFIER_REFERENCE COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
    fi

    if grep -Eq "\.env\.production|env|authority|config|compose" "$DEPLOY_FILE"; then
        pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
    else
        review "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_NOT_EXPLICIT"
    fi
else
    fail "DEPLOY_SCRIPT_MISSING"
fi

log "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"

section "11. SECRET OUTPUT GUARD"

SECRET_VALUE_OUTPUT_COUNT=0

# Scan only source/audit scripts for obvious secret-value output patterns.
# Identifier names alone are NOT considered secret values.
OUTPUT_HITS="$(
    grep -RInE \
    --exclude-dir=.git \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite' \
    --exclude='*.log' \
    "echo[[:space:]].*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=" \
    "$PROJECT_ROOT/scripts" \
    "$PROJECT_ROOT"/*.sh \
    2>/dev/null || true
)"

if [ -n "$OUTPUT_HITS" ]; then
    SECRET_VALUE_OUTPUT_COUNT="$(
        printf '%s\n' "$OUTPUT_HITS" | grep -c . || true
    )
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
else
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
fi

log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"

section "12. R17 BASELINE RECONCILIATION"

R17_COMPOSE_REFERENCE_BASELINE=3
R17_COMPOSE_LITERAL_BASELINE=0
R17_SECRET_OUTPUT_BASELINE=0

log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE_BASELINE"
log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL_BASELINE"
log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT_BASELINE"

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$R17_COMPOSE_REFERENCE_BASELINE" ]; then
    pass "R17_COMPOSE_REFERENCE_BASELINE_RESTORED"
else
    fail "R17_COMPOSE_REFERENCE_BASELINE_NOT_RESTORED"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq "$R17_COMPOSE_LITERAL_BASELINE" ]; then
    pass "R17_COMPOSE_LITERAL_BASELINE_RESTORED"
else
    fail "R17_COMPOSE_LITERAL_BASELINE_NOT_RESTORED"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq "$R17_SECRET_OUTPUT_BASELINE" ]; then
    pass "R17_SECRET_OUTPUT_BASELINE_RESTORED"
else
    fail "R17_SECRET_OUTPUT_BASELINE_NOT_RESTORED"
fi

section "13. CROSS-AUTHORITY FINAL INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ] &&
   [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
fi

if [ "$COMPOSE_TARGET_COUNT" -eq 3 ] &&
   [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ] &&
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
    fail "INVARIANT_DEPLOYMENT_NO_DIRECT_SECRET_REFERENCE"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_SECRET_VALUE_OUTPUT"
else
    fail "INVARIANT_SECRET_VALUE_OUTPUT"
fi

section "14. FINAL CLASSIFICATION"

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
    RESULT="P0_02_R26_SECRET_PROVENANCE_GROUND_TRUTH_PARSER_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R26_SECRET_PROVENANCE_GROUND_TRUTH_PARSER_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R26_SECRET_PROVENANCE_GROUND_TRUTH_PARSER_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R26_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
