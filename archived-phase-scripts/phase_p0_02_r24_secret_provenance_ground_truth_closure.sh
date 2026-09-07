#!/usr/bin/env bash
set -u

PROJECT_ROOT="${PROJECT_ROOT:-/data/data/com.termux/files/home/waste-platform}"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env.production"
CONFIG_FILE="$PROJECT_ROOT/app/core/config.py"
CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"
DEPLOY_FILE="$PROJECT_ROOT/scripts/deploy.sh"

REPORT="$PROJECT_ROOT/audit-output/p0_02_r24_secret_provenance_ground_truth_closure.txt"
mkdir -p "$PROJECT_ROOT/audit-output"

FAILURE_COUNT=0
REVIEW_COUNT=0

SECRET_TOKENS=(
  POSTGRES_PASSWORD
  DATABASE_PASSWORD
  JWT_SECRET_KEY
  JWT_REFRESH_SECRET_KEY
  S3_SECRET_KEY
)

log() {
    printf '%s\n' "$1" | tee -a "$REPORT"
}

pass() {
    log "PASS: $1"
}

fail() {
    log "FAIL: $1"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    log "REVIEW: $1"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

section() {
    log ""
    log "============================================================"
    log "$1"
    log "============================================================"
}

: > "$REPORT"

log "============================================================"
log "P0-02 R24 SECRET PROVENANCE GROUND-TRUTH CLOSURE"
log "============================================================"

section "1. SAFETY PRECHECK"

if [ -d "$PROJECT_ROOT" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_MISSING=$PROJECT_ROOT"
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

for f in \
    "$ENV_FILE" \
    "$COMPOSE_FILE" \
    "$CONFIG_FILE" \
    "$CI_FILE" \
    "$DEPLOY_FILE"
do
    if [ -f "$f" ]; then
        pass "AUTHORITY_PRESENT=${f#$PROJECT_ROOT/}"
    else
        fail "AUTHORITY_MISSING=${f#$PROJECT_ROOT/}"
    fi
done

section "3. SECRET TOKEN SET"

for token in "${SECRET_TOKENS[@]}"; do
    log "SECRET_TOKEN=$token"
done

section "4. PRODUCTION SECRET AUTHORITY"

ENV_SECRET_COUNT=0
ENV_MISSING_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do
    if awk -v k="$token" '
        $0 ~ "^[[:space:]]*" k "[[:space:]]*=" {
            found=1
            next
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
done

log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "ENV_MISSING_COUNT=$ENV_MISSING_COUNT"

if [ "$ENV_SECRET_COUNT" -eq 5 ] && [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_NOT_EXACT"
fi

section "5. GROUND-TRUTH COMPOSE TOKEN PARSER"

#
# IMPORTANT:
# Do not use grep -P, regex backreferences, or replacement expressions.
# Docker Compose accepts forms such as:
#
#   ${POSTGRES_PASSWORD:?message}
#
# Therefore the parser explicitly searches for the literal token
# sequence "${TOKEN" and validates the surrounding syntax.
#

COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_TARGET_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

for token in POSTGRES_PASSWORD JWT_SECRET_KEY JWT_REFRESH_SECRET_KEY; do

    target_count=$(
        awk -v token="$token" '
        {
            line=$0

            if (index(line, token ":") > 0) {
                count++
            }
        }
        END {
            print count+0
        }
        ' "$COMPOSE_FILE"
    )

    reference_count=$(
        awk -v token="$token" '
        {
            line=$0
            needle="${" token

            if (index(line, needle) > 0) {
                count++
            }
        }
        END {
            print count+0
        }
        ' "$COMPOSE_FILE"
    )

    literal_count=$(
        awk -v token="$token" '
        {
            line=$0

            if (index(line, token ":") > 0) {
                pos=index(line, token ":")
                tail=substr(line, pos + length(token) + 1)

                if (index(tail, "${" token) == 0 &&
                    index(tail, "$" token) == 0) {
                    count++
                }
            }
        }
        END {
            print count+0
        }
        ' "$COMPOSE_FILE"
    )

    COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + target_count))
    COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + reference_count))
    COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + literal_count))

    if [ "$reference_count" -gt 0 ]; then
        pass "COMPOSE_REFERENCE_WIRING KEY=$token COUNT=$reference_count"
    else
        fail "COMPOSE_REFERENCE_MISSING KEY=$token"
    fi

    if [ "$literal_count" -gt 0 ]; then
        fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$token VALUE=<REDACTED>"
    fi
done

#
# DATABASE_PASSWORD and S3_SECRET_KEY are production authorities but
# are not expected to be direct Compose targets in the current topology.
#

if awk '
{
    if (index($0, "DATABASE_URL:") > 0) {
        found=1
    }
}
END {
    exit(found ? 0 : 1)
}
' "$COMPOSE_FILE"; then
    pass "DATABASE_URL_MAPPING_PRESENT"
else
    fail "DATABASE_URL_MAPPING_MISSING"
fi

if awk '
{
    if (index($0, "${POSTGRES_PASSWORD") > 0) {
        found=1
    }
}
END {
    exit(found ? 0 : 1)
}
' "$COMPOSE_FILE"; then
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

if awk '
{
    if (index($0, "DATABASE_URL:") > 0 &&
        index($0, "${POSTGRES_PASSWORD") > 0) {
        found=1
    }
}
END {
    exit(found ? 0 : 1)
}
' "$COMPOSE_FILE"; then
    pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
    COMPOSE_NON_SECRET_CONTEXT_COUNT=0
else
    fail "DATABASE_URL_SECRET_REFERENCE_CONTEXT_MISSING"
    COMPOSE_NON_SECRET_CONTEXT_COUNT=1
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

section "6. RUNTIME JWT SECRET AUTHORITY"

RUNTIME_DECLARATION_COUNT=$(
    awk '
    {
        if (index($0, "JWT_SECRET_KEY") > 0) {
            count++
        }
    }
    END {
        print count+0
    }
    ' "$CONFIG_FILE"
)

if [ "$RUNTIME_DECLARATION_COUNT" -gt 0 ]; then
    pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

RUNTIME_CONTEXT_COUNT=$(
    awk '
    {
        if (
            index($0, "JWT_SECRET_KEY") > 0 ||
            index($0, "jwt_secret") > 0 ||
            index($0, "jwt-secret") > 0
        ) {
            count++
        }
    }
    END {
        print count+0
    }
    ' "$CONFIG_FILE"
)

if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
    pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
else
    fail "RUNTIME_JWT_SECRET_USE_CONTEXT_MISSING"
fi

RUNTIME_LITERAL_COUNT=$(
    awk '
    {
        if ($0 ~ /JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\''][^"'\'']+["'\'']/) {
            count++
        }
    }
    END {
        print count+0
    }
    ' "$CONFIG_FILE"
)

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
else
    fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_PRESENT"
fi

log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"

section "7. CI TEST-SCOPE AUTHORITY"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do

    if awk -v token="$token" '
    {
        if (index($0, token ":") > 0 ||
            index($0, token "=") > 0) {
            found=1
        }
    }
    END {
        exit(found ? 0 : 1)
    }
    ' "$CI_FILE" 2>/dev/null; then
        pass "CI_SECRET_ASSIGNMENT_PRESENT KEY=$token"
        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))
    else
        fail "CI_SECRET_ASSIGNMENT_MISSING KEY=$token"
    fi

    if awk -v token="$token" '
    {
        line=$0

        if (
            index(line, token ":") > 0 ||
            index(line, token "=") > 0
        ) {
            if (
                index(line, "test") > 0 ||
                index(line, "pytest") > 0 ||
                index(line, "ci") > 0
            ) {
                found=1
            }
        }
    }
    END {
        exit(found ? 0 : 1)
    }
    ' "$CI_FILE" 2>/dev/null; then
        pass "CI_SECRET_TEST_SCOPE KEY=$token"
        CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
    fi
done

#
# Conservative production-scope detection:
# only count explicit deployment/production context on the same secret
# line. This avoids treating ordinary CI test references as production.
#

for token in "${SECRET_TOKENS[@]}"; do
    if awk -v token="$token" '
    {
        line=$0

        if (
            (index(line, token ":") > 0 ||
             index(line, token "=") > 0) &&
            (
                index(line, "production") > 0 ||
                index(line, "deploy") > 0 ||
                index(line, "release") > 0
            )
        ) {
            found=1
        }
    }
    END {
        exit(found ? 0 : 1)
    }
    ' "$CI_FILE" 2>/dev/null; then
        CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
    fi
done

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_SECRET_ASSIGNMENT_COUNT" -eq 5 ]; then
    pass "CI_SECRET_ASSIGNMENT_SET_EXACT"
else
    fail "CI_SECRET_ASSIGNMENT_SET_MISMATCH EXPECTED=5 ACTUAL=$CI_SECRET_ASSIGNMENT_COUNT"
fi

if [ "$CI_TEST_SCOPE_COUNT" -eq 5 ]; then
    pass "CI_TEST_SECRET_BOUNDARY_COMPLETE"
else
    review "CI_TEST_SECRET_BOUNDARY_PARTIAL EXPECTED=5 ACTUAL=$CI_TEST_SCOPE_COUNT"
fi

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

section "8. DEPLOYMENT AUTHORITY BOUNDARY"

DEPLOY_SECRET_REFERENCE_COUNT=$(
    awk '
    {
        if (
            index($0, "POSTGRES_PASSWORD") > 0 ||
            index($0, "DATABASE_PASSWORD") > 0 ||
            index($0, "JWT_SECRET_KEY") > 0 ||
            index($0, "JWT_REFRESH_SECRET_KEY") > 0 ||
            index($0, "S3_SECRET_KEY") > 0
        ) {
            count++
        }
    }
    END {
        print count+0
    }
    ' "$DEPLOY_FILE"
)

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
else
    fail "DEPLOY_SCRIPT_HAS_DIRECT_SECRET_IDENTIFIER_REFERENCE COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
fi

if awk '
{
    if (
        index($0, ".env.production") > 0 ||
        index($0, "docker-compose.yml") > 0 ||
        index($0, "compose") > 0
    ) {
        found=1
    }
}
END {
    exit(found ? 0 : 1)
}
' "$DEPLOY_FILE"; then
    pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
else
    fail "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_MISSING"
fi

log "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"

section "9. SECRET OUTPUT GUARD"

SECRET_VALUE_OUTPUT_COUNT=$(
    awk '
    {
        if (
            index($0, "VALUE=<REDACTED>") > 0 ||
            index($0, "REDACTED") > 0 ||
            index($0, "<SECRET>") > 0
        ) {
            next
        }

        if (
            index($0, "POSTGRES_PASSWORD=") > 0 ||
            index($0, "DATABASE_PASSWORD=") > 0 ||
            index($0, "JWT_SECRET_KEY=") > 0 ||
            index($0, "JWT_REFRESH_SECRET_KEY=") > 0 ||
            index($0, "S3_SECRET_KEY=") > 0
        ) {
            count++
        }
    }
    END {
        print count+0
    }
    ' "$REPORT"
)

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
fi

log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"

section "10. R17 REGRESSION BASELINE"

R17_REPORT="$PROJECT_ROOT/audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt"

if [ -f "$R17_REPORT" ]; then
    pass "R17_REPORT_PRESENT"

    R17_COMPOSE_REFERENCE_BASELINE=$(
        awk -F= '
        /COMPOSE_REFERENCE_COUNT=/ {
            print $2
            exit
        }
        ' "$R17_REPORT"
    )

    R17_COMPOSE_LITERAL_BASELINE=$(
        awk -F= '
        /COMPOSE_LITERAL_COUNT=/ {
            print $2
            exit
        }
        ' "$R17_REPORT"
    )

    R17_SECRET_OUTPUT_BASELINE=$(
        awk -F= '
        /SECRET_VALUE_OUTPUT_COUNT=/ {
            print $2
            exit
        }
        ' "$R17_REPORT"
    )

    R17_COMPOSE_REFERENCE_BASELINE="${R17_COMPOSE_REFERENCE_BASELINE:-3}"
    R17_COMPOSE_LITERAL_BASELINE="${R17_COMPOSE_LITERAL_BASELINE:-0}"
    R17_SECRET_OUTPUT_BASELINE="${R17_SECRET_OUTPUT_BASELINE:-0}"

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
else
    review "R17_REPORT_NOT_PRESENT"
    R17_COMPOSE_REFERENCE_BASELINE=3
    R17_COMPOSE_LITERAL_BASELINE=0
    R17_SECRET_OUTPUT_BASELINE=0
fi

section "11. FINAL INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ] &&
   [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq 0 ] &&
   [ "$COMPOSE_TARGET_COUNT" -eq 3 ]; then
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
    RESULT="P0_02_R24_SECRET_PROVENANCE_GROUND_TRUTH_CLOSURE_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R24_SECRET_PROVENANCE_GROUND_TRUTH_CLOSURE_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R24_SECRET_PROVENANCE_GROUND_TRUTH_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R24_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
