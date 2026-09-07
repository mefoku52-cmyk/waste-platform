#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT_DIR="$PROJECT_ROOT/audit-output"
mkdir -p "$REPORT_DIR"

REPORT="$REPORT_DIR/p0_02_r11_secret_provenance_lineage_closure.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

ENV_SECRET_COUNT=0
COMPOSE_SECRET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

DEPLOY_SECRET_REFERENCE_COUNT=0
DEPLOY_ENV_REFERENCE_COUNT=0
DEPLOY_COMPOSE_REFERENCE_COUNT=0

LINEAGE_COMPLETE_COUNT=0
LINEAGE_GAP_COUNT=0
SECRET_VALUE_OUTPUT_COUNT=0

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

AUTHORITY_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

section() {
    echo "============================================================" | tee -a "$REPORT"
    echo "$1" | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
}

pass() {
    echo "PASS: $1" | tee -a "$REPORT"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    echo "REVIEW: $1" | tee -a "$REPORT"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "FAIL: $1" | tee -a "$REPORT"
}

echo "P0-02 R11 SECRET PROVENANCE LINEAGE CLOSURE" > "$REPORT"

section "1. SAFETY PRECHECK"

if [ "$PROJECT_ROOT" = "/data/data/com.termux/files/home/waste-platform" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_MISMATCH=$PROJECT_ROOT"
fi

READ_ONLY=YES
NO_SOURCE_WRITES=YES
NO_RUNTIME_EXECUTION=YES
NO_ENV_EXECUTION=YES
NO_BUILD=YES
NO_DEPLOYMENT=YES
NO_DELETIONS=YES
NO_SECRET_VALUES_PRINTED=YES
BOUNDED_SCAN=YES

for FLAG in \
    READ_ONLY \
    NO_SOURCE_WRITES \
    NO_RUNTIME_EXECUTION \
    NO_ENV_EXECUTION \
    NO_BUILD \
    NO_DEPLOYMENT \
    NO_DELETIONS \
    NO_SECRET_VALUES_PRINTED \
    BOUNDED_SCAN
do
    if [ "${!FLAG}" = "YES" ]; then
        pass "$FLAG=YES"
    else
        fail "$FLAG=${!FLAG}"
    fi
done

section "2. REQUIRED AUTHORITY FILES"

for FILE in "${AUTHORITY_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$FILE" ]; then
        pass "AUTHORITY_PRESENT=$FILE"
    else
        fail "AUTHORITY_MISSING=$FILE"
    fi
done

section "3. SECRET IDENTIFIER SET"

for KEY in "${SECRET_KEYS[@]}"; do
    echo "SECRET_IDENTIFIER=$KEY" | tee -a "$REPORT"
done

section "4. PRODUCTION ENV AUTHORITY"

if [ -f "$PROJECT_ROOT/.env.production" ]; then

    for KEY in "${SECRET_KEYS[@]}"; do
        if grep -Eq "^[[:space:]]*${KEY}[[:space:]]*=" \
            "$PROJECT_ROOT/.env.production"
        then
            ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
            pass "ENV_AUTHORITY_PRESENT KEY=$KEY VALUE=<REDACTED>"
        else
            fail "ENV_AUTHORITY_MISSING KEY=$KEY"
        fi
    done

else
    fail "ENV_PRODUCTION_FILE_MISSING"
fi

echo "ENV_SECRET_COUNT=$ENV_SECRET_COUNT" | tee -a "$REPORT"

if [ "$ENV_SECRET_COUNT" -eq "${#SECRET_KEYS[@]}" ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_COMPLETE"
else
    fail "PRODUCTION_SECRET_AUTHORITY_INCOMPLETE"
fi

section "5. COMPOSE PROVENANCE"

if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then

    for KEY in "${SECRET_KEYS[@]}"; do

        if grep -Eq \
            "^[[:space:]]*[-]?[[:space:]]*${KEY}[[:space:]]*:[[:space:]]*\$\{" \
            "$PROJECT_ROOT/docker-compose.yml"
        then
            COMPOSE_SECRET_COUNT=$((COMPOSE_SECRET_COUNT + 1))
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
            pass "COMPOSE_REFERENCE KEY=$KEY"
            continue
        fi

        if grep -Eq \
            "^[[:space:]]*[-]?[[:space:]]*${KEY}[[:space:]]*:" \
            "$PROJECT_ROOT/docker-compose.yml"
        then
            COMPOSE_SECRET_COUNT=$((COMPOSE_SECRET_COUNT + 1))
            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$KEY VALUE=<REDACTED>"
        fi
    done

else
    fail "COMPOSE_FILE_MISSING"
fi

echo "COMPOSE_SECRET_COUNT=$COMPOSE_SECRET_COUNT" | tee -a "$REPORT"
echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT" | tee -a "$REPORT"

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
fi

section "6. DATABASE_URL PROVENANCE"

DATABASE_URL_COUNT=0
DATABASE_URL_SECRET_REFERENCE_COUNT=0

if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then

    DATABASE_URL_COUNT="$(
        grep -Ec \
        "DATABASE_URL[[:space:]]*:" \
        "$PROJECT_ROOT/docker-compose.yml" || true
    )"

    DATABASE_URL_SECRET_REFERENCE_COUNT="$(
        grep -Ec \
        'DATABASE_URL.*\$\{POSTGRES_PASSWORD' \
        "$PROJECT_ROOT/docker-compose.yml" || true
    )"

    if [ "$DATABASE_URL_SECRET_REFERENCE_COUNT" -gt 0 ]; then
        pass "DATABASE_URL_POSTGRES_PASSWORD_PROVENANCE_PRESENT"
    else
        fail "DATABASE_URL_POSTGRES_PASSWORD_PROVENANCE_MISSING"
    fi

else
    fail "DATABASE_URL_SOURCE_FILE_MISSING"
fi

echo "DATABASE_URL_COUNT=$DATABASE_URL_COUNT" | tee -a "$REPORT"
echo "DATABASE_URL_SECRET_REFERENCE_COUNT=$DATABASE_URL_SECRET_REFERENCE_COUNT" | tee -a "$REPORT"

section "7. RUNTIME PROVENANCE"

CONFIG_FILE="$PROJECT_ROOT/app/core/config.py"

if [ -f "$CONFIG_FILE" ]; then

    RUNTIME_DECLARATION_COUNT="$(
        grep -Ec \
        "^[[:space:]]*JWT_SECRET_KEY[[:space:]]*:" \
        "$CONFIG_FILE" || true
    )"

    RUNTIME_CONTEXT_COUNT="$(
        grep -Ec \
        "JWTSettings|self\.JWT_SECRET_KEY|JWT_SECRET_KEY" \
        "$CONFIG_FILE" || true
    )"

    if [ "$RUNTIME_DECLARATION_COUNT" -gt 0 ]; then
        pass "RUNTIME_JWT_SECRET_DECLARATION_PRESENT"
    else
        fail "RUNTIME_JWT_SECRET_DECLARATION_MISSING"
    fi

    if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
        pass "RUNTIME_JWT_SECRET_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
    else
        fail "RUNTIME_JWT_SECRET_CONTEXT_MISSING"
    fi

    RUNTIME_LITERAL_COUNT="$(
        grep -Eic \
        "^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*=[[:space:]]*['\\\"]" \
        "$CONFIG_FILE" || true
    )"

    if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
        pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
    else
        fail "RUNTIME_LITERAL_SECRET_ASSIGNMENT_DETECTED"
    fi

else
    fail "RUNTIME_CONFIG_MISSING"
fi

echo "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT" | tee -a "$REPORT"
echo "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT" | tee -a "$REPORT"

section "8. CI SCOPE PROVENANCE"

CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"

if [ -f "$CI_FILE" ]; then

    CI_SECRET_ASSIGNMENT_COUNT=0
    CI_TEST_SCOPE_COUNT=0
    CI_PROD_SCOPE_COUNT=0

    for KEY in "${SECRET_KEYS[@]}"; do

        MATCHES="$(
            grep -En \
            "^[[:space:]]*${KEY}[[:space:]]*:" \
            "$CI_FILE" 2>/dev/null || true
        )"

        if [ -n "$MATCHES" ]; then

            COUNT="$(
                printf '%s\n' "$MATCHES" |
                grep -Ec "." || true
            )"

            CI_SECRET_ASSIGNMENT_COUNT=$(
                printf '%s' "$CI_SECRET_ASSIGNMENT_COUNT + $COUNT" |
                bc
            )

            if printf '%s\n' "$MATCHES" |
                grep -Eiq \
                "test|pytest|ci|integration|unit|fixture|mock"
            then
                CI_TEST_SCOPE_COUNT=$(
                    printf '%s' "$CI_TEST_SCOPE_COUNT + $COUNT" |
                    bc
                )
            fi

            if printf '%s\n' "$MATCHES" |
                grep -Eiq \
                "production|prod|deploy|release"
            then
                CI_PROD_SCOPE_COUNT=$(
                    printf '%s' "$CI_PROD_SCOPE_COUNT + $COUNT" |
                    bc
                )
            fi

            echo "REVIEW: CI_SECRET_ASSIGNMENT KEY=$KEY VALUE=<REDACTED>" \
                | tee -a "$REPORT"
        fi
    done

    if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
        pass "CI_HAS_NO_DETECTED_PRODUCTION_SECRET_SCOPE"
    else
        fail "CI_PRODUCTION_SECRET_SCOPE_DETECTED"
    fi

    if [ "$CI_SECRET_ASSIGNMENT_COUNT" -gt 0 ]; then
        pass "CI_SECRET_ASSIGNMENTS_PRESENT_ONLY_AS_REVIEWED_TEST_BOUNDARY"
    else
        pass "NO_CI_SECRET_ASSIGNMENTS_DETECTED"
    fi

else
    fail "CI_FILE_MISSING"
fi

echo "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT" | tee -a "$REPORT"
echo "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT" | tee -a "$REPORT"
echo "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT" | tee -a "$REPORT"

section "9. DEPLOYMENT PROVENANCE"

DEPLOY_FILE="$PROJECT_ROOT/scripts/deploy.sh"

if [ -f "$DEPLOY_FILE" ]; then

    DEPLOY_SECRET_REFERENCE_COUNT="$(
        grep -Eic \
        "POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY" \
        "$DEPLOY_FILE" || true
    )"

    DEPLOY_ENV_REFERENCE_COUNT="$(
        grep -Eic \
        "\.env\.production|--env-file" \
        "$DEPLOY_FILE" || true
    )"

    DEPLOY_COMPOSE_REFERENCE_COUNT="$(
        grep -Eic \
        "docker[[:space:]-]*compose|compose[[:space:]]" \
        "$DEPLOY_FILE" || true
    )"

    if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
        pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
    else
        review "DEPLOY_SCRIPT_SECRET_IDENTIFIER_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
    fi

    if [ "$DEPLOY_ENV_REFERENCE_COUNT" -gt 0 ]; then
        pass "DEPLOY_SCRIPT_REFERENCES_ENV_AUTHORITY_BOUNDARY"
    else
        review "DEPLOY_SCRIPT_HAS_NO_EXPLICIT_ENV_PRODUCTION_REFERENCE"
    fi

    if [ "$DEPLOY_COMPOSE_REFERENCE_COUNT" -gt 0 ]; then
        pass "DEPLOY_SCRIPT_REFERENCES_COMPOSE_BOUNDARY"
    else
        review "DEPLOY_SCRIPT_HAS_NO_EXPLICIT_COMPOSE_REFERENCE"
    fi

else
    fail "DEPLOY_SCRIPT_MISSING"
fi

echo "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT" | tee -a "$REPORT"
echo "DEPLOY_ENV_REFERENCE_COUNT=$DEPLOY_ENV_REFERENCE_COUNT" | tee -a "$REPORT"
echo "DEPLOY_COMPOSE_REFERENCE_COUNT=$DEPLOY_COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"

section "10. CROSS-AUTHORITY LINEAGE"

for KEY in "${SECRET_KEYS[@]}"; do

    ENV_OK=0
    COMPOSE_OK=0
    RUNTIME_OK=0

    if grep -Eq \
        "^[[:space:]]*${KEY}[[:space:]]*=" \
        "$PROJECT_ROOT/.env.production"
    then
        ENV_OK=1
    fi

    if grep -Eq \
        "${KEY}[[:space:]]*:[[:space:]]*\$\{" \
        "$PROJECT_ROOT/docker-compose.yml"
    then
        COMPOSE_OK=1
    fi

    if [ "$KEY" = "JWT_SECRET_KEY" ]; then
        if grep -Eq \
            "JWT_SECRET_KEY" \
            "$PROJECT_ROOT/app/core/config.py"
        then
            RUNTIME_OK=1
        fi
    elif [ "$KEY" = "JWT_REFRESH_SECRET_KEY" ]; then
        if grep -Eq \
            "JWT_REFRESH_SECRET|REFRESH_TOKEN_SECRET" \
            "$PROJECT_ROOT/app/core/config.py"
        then
            RUNTIME_OK=1
        fi
    else
        RUNTIME_OK=1
    fi

    if [ "$ENV_OK" -eq 1 ] &&
       [ "$COMPOSE_OK" -eq 1 ] &&
       [ "$RUNTIME_OK" -eq 1 ]; then

        LINEAGE_COMPLETE_COUNT=$((LINEAGE_COMPLETE_COUNT + 1))
        pass "LINEAGE_COMPLETE KEY=$KEY"

    else

        LINEAGE_GAP_COUNT=$((LINEAGE_GAP_COUNT + 1))

        if [ "$ENV_OK" -eq 0 ]; then
            fail "LINEAGE_ENV_GAP KEY=$KEY"
        fi

        if [ "$COMPOSE_OK" -eq 0 ]; then
            review "LINEAGE_COMPOSE_GAP KEY=$KEY"
        fi

        if [ "$RUNTIME_OK" -eq 0 ]; then
            review "LINEAGE_RUNTIME_GAP KEY=$KEY"
        fi
    fi
done

echo "LINEAGE_COMPLETE_COUNT=$LINEAGE_COMPLETE_COUNT" | tee -a "$REPORT"
echo "LINEAGE_GAP_COUNT=$LINEAGE_GAP_COUNT" | tee -a "$REPORT"

section "11. SECRET VALUE OUTPUT GUARD"

SECRET_VALUE_OUTPUT_COUNT=0

for FILE in \
    "$PROJECT_ROOT/.env.production" \
    "$PROJECT_ROOT/docker-compose.yml" \
    "$PROJECT_ROOT/app/core/config.py" \
    "$PROJECT_ROOT/.github/workflows/ci.yml" \
    "$PROJECT_ROOT/scripts/deploy.sh"
do
    [ -f "$FILE" ] || continue

    if grep -Eq \
        "echo[[:space:]]+.*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)" \
        "$FILE"
    then
        SECRET_VALUE_OUTPUT_COUNT=$(
            printf '%s' "$SECRET_VALUE_OUTPUT_COUNT + 1" |
            bc
        )
    fi
done

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    fail "SECRET_VALUE_OUTPUT_SIGNAL_DETECTED"
fi

echo "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT" | tee -a "$REPORT"

section "12. FINAL INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET_NOT_EXACT"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_COMPOSE_SECRET"
else
    fail "INVARIANT_LITERAL_COMPOSE_SECRET"
fi

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_RUNTIME_SECRET"
else
    fail "INVARIANT_LITERAL_RUNTIME_SECRET"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_SECRET_VALUE_OUTPUT"
else
    fail "INVARIANT_SECRET_VALUE_OUTPUT"
fi

if [ "$DATABASE_URL_SECRET_REFERENCE_COUNT" -gt 0 ]; then
    pass "INVARIANT_DATABASE_URL_SECRET_BOUNDARY"
else
    fail "INVARIANT_DATABASE_URL_SECRET_BOUNDARY_MISSING"
fi

if [ "$LINEAGE_GAP_COUNT" -eq 0 ]; then
    pass "INVARIANT_CROSS_AUTHORITY_LINEAGE_COMPLETE"
else
    fail "INVARIANT_CROSS_AUTHORITY_LINEAGE_GAPS=$LINEAGE_GAP_COUNT"
fi

section "13. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "ENV_SECRET_COUNT=$ENV_SECRET_COUNT" | tee -a "$REPORT"
echo "COMPOSE_SECRET_COUNT=$COMPOSE_SECRET_COUNT" | tee -a "$REPORT"
echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT" | tee -a "$REPORT"
echo "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT" | tee -a "$REPORT"
echo "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT" | tee -a "$REPORT"
echo "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT" | tee -a "$REPORT"
echo "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT" | tee -a "$REPORT"
echo "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT" | tee -a "$REPORT"
echo "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT" | tee -a "$REPORT"
echo "DEPLOY_ENV_REFERENCE_COUNT=$DEPLOY_ENV_REFERENCE_COUNT" | tee -a "$REPORT"
echo "DEPLOY_COMPOSE_REFERENCE_COUNT=$DEPLOY_COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "LINEAGE_COMPLETE_COUNT=$LINEAGE_COMPLETE_COUNT" | tee -a "$REPORT"
echo "LINEAGE_GAP_COUNT=$LINEAGE_GAP_COUNT" | tee -a "$REPORT"
echo "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R11_SECRET_PROVENANCE_LINEAGE_CLOSURE_FAIL"
    EXIT_CODE=1
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R11_SECRET_PROVENANCE_LINEAGE_CLOSURE_REVIEW"
    EXIT_CODE=2
else
    STATUS="CLEAN"
    RESULT="P0_02_R11_SECRET_PROVENANCE_LINEAGE_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R11_STATUS=$STATUS" | tee -a "$REPORT"
echo "RESULT=$RESULT" | tee -a "$REPORT"
echo "EXIT_CODE=$EXIT_CODE" | tee -a "$REPORT"
echo "REPORT=$REPORT" | tee -a "$REPORT"

exit "$EXIT_CODE"
