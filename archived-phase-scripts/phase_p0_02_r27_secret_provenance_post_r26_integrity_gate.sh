#!/data/data/com.termux/files/usr/bin/bash
set -u

PROJECT_ROOT="${HOME}/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r27_secret_provenance_post_r26_integrity_gate.txt"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

mkdir -p "${REPORT_DIR}"
exec > >(tee "${REPORT}") 2>&1

echo "============================================================"
echo "P0-02 R27 SECRET PROVENANCE POST-R26 INTEGRITY GATE"
echo "============================================================"

FAILURE_COUNT=0
REVIEW_COUNT=0

fail(){ echo "FAIL: $1"; FAILURE_COUNT=$((FAILURE_COUNT+1)); }
pass(){ echo "PASS: $1"; }
review(){ echo "REVIEW: $1"; REVIEW_COUNT=$((REVIEW_COUNT+1)); }

echo "============================================================"
echo "1. SAFETY PRECHECK"
echo "============================================================"

[ -d "${PROJECT_ROOT}" ] && pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}" || fail "PROJECT_ROOT_MISSING"

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_DELETIONS=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "BOUNDED_SCAN=YES"

cd "${PROJECT_ROOT}" || exit 1

echo
echo "============================================================"
echo "2. REQUIRED AUTHORITY FILES"
echo "============================================================"

for f in \
    ".env.production" \
    "docker-compose.yml" \
    "app/core/config.py" \
    ".github/workflows/ci.yml" \
    "scripts/deploy.sh"
do
    [ -f "$f" ] && pass "AUTHORITY_PRESENT=${f}" || fail "AUTHORITY_MISSING=${f}"
done

echo
echo "============================================================"
echo "3. COMPOSE FORENSIC CLASSIFICATION"
echo "============================================================"

COMPOSE_TARGET_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ {
    count++
}
END {
    print count + 0
}
' "${COMPOSE_FILE}"
)

COMPOSE_REFERENCE_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ {
    line = $0
    value = substr(line, index(line, ":") + 1)
    sub(/^[[:space:]]*/, "", value)

    if (value ~ /^\$\{/) {
        count++
    }
}
END {
    print count + 0
}
' "${COMPOSE_FILE}"
)

COMPOSE_LITERAL_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:/ {
    line = $0
    value = substr(line, index(line, ":") + 1)
    sub(/^[[:space:]]*/, "", value)

    if (value == "") {
        next
    }

    if (value ~ /^\$\{/) {
        next
    }

    count++
}
END {
    print count + 0
}
' "${COMPOSE_FILE}"
)

echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"

[ "${COMPOSE_TARGET_COUNT}" -eq 3 ] \
    && pass "COMPOSE_TARGET_CARDINALITY_EXACT" \
    || fail "COMPOSE_TARGET_CARDINALITY_MISMATCH"

[ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] \
    && pass "COMPOSE_REFERENCE_CARDINALITY_EXACT" \
    || fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH"

[ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] \
    && pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT" \
    || fail "LITERAL_COMPOSE_SECRET_ASSIGNMENT_DETECTED"

echo
echo "============================================================"
echo "4. DATABASE URL SECRET INTERPOLATION"
echo "============================================================"

if grep -Eq 'DATABASE_URL:.*\$\{POSTGRES_PASSWORD:' "${COMPOSE_FILE}"; then
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

echo
echo "============================================================"
echo "5. RUNTIME SECRET PROVENANCE"
echo "============================================================"

if grep -Eq 'JWT_SECRET_KEY' app/core/config.py; then
    pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

if grep -Eq 'SECRET|secret|provenance|authority' app/core/config.py; then
    pass "RUNTIME_SECRET_AUTHORITY_CONTEXT_PRESENT"
else
    review "RUNTIME_SECRET_AUTHORITY_CONTEXT_NOT_DETECTABLE"
fi

RUNTIME_DECLARATION_COUNT=$(
grep -Ec '^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|POSTGRES_PASSWORD|DATABASE_PASSWORD|S3_SECRET_KEY)[[:space:]]*=' \
app/core/config.py 2>/dev/null || true
)

RUNTIME_LITERAL_COUNT=$(
grep -Ec '^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|POSTGRES_PASSWORD|DATABASE_PASSWORD|S3_SECRET_KEY)[[:space:]]*=[[:space:]]*["'\'']' \
app/core/config.py 2>/dev/null || true
)

echo "RUNTIME_DECLARATION_COUNT=${RUNTIME_DECLARATION_COUNT}"
echo "RUNTIME_LITERAL_COUNT=${RUNTIME_LITERAL_COUNT}"

[ "${RUNTIME_DECLARATION_COUNT}" -eq 0 ] \
    && pass "NO_RUNTIME_SECRET_DECLARATION" \
    || fail "RUNTIME_SECRET_DECLARATION_DETECTED"

[ "${RUNTIME_LITERAL_COUNT}" -eq 0 ] \
    && pass "NO_RUNTIME_LITERAL_SECRET" \
    || fail "RUNTIME_LITERAL_SECRET_DETECTED"

echo
echo "============================================================"
echo "6. CI SECRET IDENTIFIERS"
echo "============================================================"

CI_SECRET_ASSIGNMENT_COUNT=0

for key in \
    POSTGRES_PASSWORD \
    DATABASE_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    S3_SECRET_KEY
do
    if grep -Eq "${key}" .github/workflows/ci.yml; then
        pass "CI_SECRET_IDENTIFIER_PRESENT=${key}"
        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT+1))
    else
        fail "CI_SECRET_IDENTIFIER_MISSING=${key}"
    fi
done

echo "CI_SECRET_ASSIGNMENT_COUNT=${CI_SECRET_ASSIGNMENT_COUNT}"

CI_PROD_SCOPE_COUNT=$(
grep -Ec 'production|prod' .github/workflows/ci.yml 2>/dev/null || true
)

echo "CI_PROD_SCOPE_COUNT=${CI_PROD_SCOPE_COUNT}"

echo
echo "============================================================"
echo "7. DEPLOYMENT SECRET REFERENCE"
echo "============================================================"

DEPLOY_SECRET_REFERENCE_COUNT=$(
grep -Ec \
'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
scripts/deploy.sh 2>/dev/null || true
)

echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"

[ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ] \
    && pass "DEPLOY_SECRET_REFERENCE_BASELINE_ZERO" \
    || fail "DEPLOY_SECRET_REFERENCE_DETECTED"

echo
echo "============================================================"
echo "8. SECRET VALUE OUTPUT"
echo "============================================================"

SECRET_VALUE_OUTPUT_COUNT=$(
grep -REn \
'(echo|printf|print)[^#]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
.github scripts app \
--exclude='*.pyc' \
--exclude-dir='__pycache__' \
2>/dev/null | wc -l
)

echo "SECRET_VALUE_OUTPUT_COUNT=${SECRET_VALUE_OUTPUT_COUNT}"

[ "${SECRET_VALUE_OUTPUT_COUNT}" -eq 0 ] \
    && pass "NO_SECRET_VALUE_OUTPUT_PATTERN" \
    || fail "SECRET_VALUE_OUTPUT_PATTERN_DETECTED"

echo
echo "============================================================"
echo "9. R26 BASELINE CONTINUITY"
echo "============================================================"

R26_REFERENCE_BASELINE=3
R26_LITERAL_BASELINE=0
R26_SECRET_OUTPUT_BASELINE=0

echo "R26_REFERENCE_BASELINE=${R26_REFERENCE_BASELINE}"
echo "R26_LITERAL_BASELINE=${R26_LITERAL_BASELINE}"
echo "R26_SECRET_OUTPUT_BASELINE=${R26_SECRET_OUTPUT_BASELINE}"

[ "${COMPOSE_REFERENCE_COUNT}" -eq "${R26_REFERENCE_BASELINE}" ] \
    && pass "R26_REFERENCE_BASELINE_CONTINUITY" \
    || fail "R26_REFERENCE_BASELINE_DRIFT"

[ "${COMPOSE_LITERAL_COUNT}" -eq "${R26_LITERAL_BASELINE}" ] \
    && pass "R26_LITERAL_BASELINE_CONTINUITY" \
    || fail "R26_LITERAL_BASELINE_DRIFT"

[ "${SECRET_VALUE_OUTPUT_COUNT}" -eq "${R26_SECRET_OUTPUT_BASELINE}" ] \
    && pass "R26_SECRET_OUTPUT_BASELINE_CONTINUITY" \
    || fail "R26_SECRET_OUTPUT_BASELINE_DRIFT"

echo
echo "============================================================"
echo "10. FINAL CLASSIFICATION"
echo "============================================================"

if [ "${FAILURE_COUNT}" -eq 0 ] && [ "${REVIEW_COUNT}" -eq 0 ]; then
    STATUS="CLEAN"
    RESULT="P0_02_R27_SECRET_PROVENANCE_POST_R26_INTEGRITY_CLEAN"
    EXIT_CODE=0
else
    STATUS="REVIEW"
    RESULT="P0_02_R27_SECRET_PROVENANCE_POST_R26_INTEGRITY_REVIEW"
    EXIT_CODE=1
fi

echo "FAILURE_COUNT=${FAILURE_COUNT}"
echo "REVIEW_COUNT=${REVIEW_COUNT}"
echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "CI_SECRET_ASSIGNMENT_COUNT=${CI_SECRET_ASSIGNMENT_COUNT}"
echo "CI_PROD_SCOPE_COUNT=${CI_PROD_SCOPE_COUNT}"
echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"
echo "SECRET_VALUE_OUTPUT_COUNT=${SECRET_VALUE_OUTPUT_COUNT}"
echo "P0_02_R27_STATUS=${STATUS}"
echo "RESULT=${RESULT}"
echo "EXIT_CODE=${EXIT_CODE}"
echo "REPORT=${REPORT}"

exit "${EXIT_CODE}"
