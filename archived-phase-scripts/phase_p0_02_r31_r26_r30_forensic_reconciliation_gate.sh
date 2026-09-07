#!/data/data/com.termux/files/usr/bin/bash
set -u

PROJECT_ROOT="${HOME}/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r31_r26_r30_forensic_reconciliation_gate.txt"

mkdir -p "${REPORT_DIR}"
exec > >(tee "${REPORT}") 2>&1

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

echo "============================================================"
echo "P0-02 R31 R26-R30 FORENSIC RECONCILIATION GATE"
echo "============================================================"

echo
echo "============================================================"
echo "1. SAFETY PRECHECK"
echo "============================================================"

if [ -d "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
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

cd "${PROJECT_ROOT}" || exit 1

echo
echo "============================================================"
echo "2. AUTHORITY FILE PRESENCE"
echo "============================================================"

for f in \
    ".env.production" \
    "docker-compose.yml" \
    "app/core/config.py" \
    ".github/workflows/ci.yml" \
    "scripts/deploy.sh"
do
    if [ -f "${f}" ]; then
        pass "AUTHORITY_PRESENT=${f}"
    else
        fail "AUTHORITY_MISSING=${f}"
    fi
done

echo
echo "============================================================"
echo "3. .ENV.PRODUCTION KEY SET"
echo "============================================================"

ENV_SECRET_COUNT=0

for key in \
    POSTGRES_PASSWORD \
    DATABASE_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    S3_SECRET_KEY
do
    if grep -Eq \
        "^[[:space:]]*${key}[[:space:]]*=[[:space:]]*[^[:space:]#]" \
        .env.production 2>/dev/null
    then
        pass "ENV_AUTHORITY_PRESENT=${key}"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING_OR_EMPTY=${key}"
    fi
done

echo "ENV_SECRET_AUTHORITY_COUNT=${ENV_SECRET_COUNT}"

if [ "${ENV_SECRET_COUNT}" -eq 5 ]; then
    pass "ENV_SECRET_AUTHORITY_CARDINALITY_EXACT"
else
    fail "ENV_SECRET_AUTHORITY_CARDINALITY_MISMATCH"
fi

echo
echo "============================================================"
echo "4. COMPOSE DIRECT SECRET TARGETS"
echo "============================================================"

COMPOSE_TARGET_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ {
    count++
}
END {
    print count + 0
}
' docker-compose.yml 2>/dev/null
)

echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"

if [ "${COMPOSE_TARGET_COUNT}" -eq 3 ]; then
    pass "COMPOSE_TARGET_CARDINALITY_EXACT"
else
    fail "COMPOSE_TARGET_CARDINALITY_MISMATCH"
fi

echo
echo "============================================================"
echo "5. COMPOSE VALUE CLASSIFICATION"
echo "============================================================"

COMPOSE_REFERENCE_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ {
    line=$0
    value=substr(line,index(line,":")+1)
    sub(/^[[:space:]]*/,"",value)

    if (value ~ /^\$\{/) {
        count++
    }
}
END {
    print count + 0
}
' docker-compose.yml 2>/dev/null
)

COMPOSE_LITERAL_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:/ {
    line=$0
    value=substr(line,index(line,":")+1)
    sub(/^[[:space:]]*/,"",value)

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
' docker-compose.yml 2>/dev/null
)

echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"

if [ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ]; then
    pass "COMPOSE_REFERENCE_CARDINALITY_EXACT"
else
    fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH"
fi

if [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ]; then
    pass "COMPOSE_LITERAL_COUNT_ZERO"
else
    fail "COMPOSE_LITERAL_ASSIGNMENT_DETECTED"
fi

echo
echo "============================================================"
echo "6. COMPOSE KEY-BY-KEY REFERENCE PROOF"
echo "============================================================"

COMPOSE_KEY_REFERENCE_FAILURES=0

for key in \
    POSTGRES_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY
do
    if awk -v wanted="${key}" '
    $0 ~ "^[[:space:]]*" wanted "[[:space:]]*:" {
        line=$0
        value=substr(line,index(line,":")+1)
        sub(/^[[:space:]]*/,"",value)

        if (value ~ /^\$\{/) {
            found=1
        }
    }
    END {
        exit(found ? 0 : 1)
    }
    ' docker-compose.yml 2>/dev/null
    then
        pass "COMPOSE_REFERENCE_PRESENT=${key}"
    else
        fail "COMPOSE_REFERENCE_MISSING=${key}"
        COMPOSE_KEY_REFERENCE_FAILURES=$((COMPOSE_KEY_REFERENCE_FAILURES + 1))
    fi
done

echo "COMPOSE_KEY_REFERENCE_FAILURES=${COMPOSE_KEY_REFERENCE_FAILURES}"

echo
echo "============================================================"
echo "7. DATABASE_URL PROVENANCE"
echo "============================================================"

if grep -Eq \
    'DATABASE_URL:.*\$\{POSTGRES_PASSWORD:' \
    docker-compose.yml
then
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

echo
echo "============================================================"
echo "8. RUNTIME PROVENANCE"
echo "============================================================"

if grep -Eq 'JWT_SECRET_KEY' app/core/config.py; then
    pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

RUNTIME_DIRECT_ASSIGNMENT_COUNT=$(
grep -Ec \
'^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=' \
app/core/config.py 2>/dev/null || true
)

echo "RUNTIME_DIRECT_ASSIGNMENT_COUNT=${RUNTIME_DIRECT_ASSIGNMENT_COUNT}"

if [ "${RUNTIME_DIRECT_ASSIGNMENT_COUNT}" -eq 0 ]; then
    pass "NO_RUNTIME_DIRECT_SECRET_ASSIGNMENT"
else
    fail "RUNTIME_DIRECT_SECRET_ASSIGNMENT_DETECTED"
fi

echo
echo "============================================================"
echo "9. CI SECRET IDENTIFIER SET"
echo "============================================================"

CI_IDENTIFIER_COUNT=0

for key in \
    POSTGRES_PASSWORD \
    DATABASE_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    S3_SECRET_KEY
do
    if grep -Eq "${key}" .github/workflows/ci.yml 2>/dev/null; then
        pass "CI_IDENTIFIER_PRESENT=${key}"
        CI_IDENTIFIER_COUNT=$((CI_IDENTIFIER_COUNT + 1))
    else
        fail "CI_IDENTIFIER_MISSING=${key}"
    fi
done

echo "CI_IDENTIFIER_COUNT=${CI_IDENTIFIER_COUNT}"

if [ "${CI_IDENTIFIER_COUNT}" -eq 5 ]; then
    pass "CI_IDENTIFIER_CARDINALITY_EXACT"
else
    fail "CI_IDENTIFIER_CARDINALITY_MISMATCH"
fi

echo
echo "============================================================"
echo "10. DEPLOY SECRET REFERENCE"
echo "============================================================"

DEPLOY_SECRET_REFERENCE_COUNT=$(
grep -Ec \
'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
scripts/deploy.sh 2>/dev/null || true
)

echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"

if [ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ]; then
    pass "DEPLOY_SECRET_REFERENCE_COUNT_ZERO"
else
    review "DEPLOY_SECRET_IDENTIFIER_PRESENT"
fi

echo
echo "============================================================"
echo "11. SECRET OUTPUT FORENSIC RECHECK"
echo "============================================================"

echo "The previous R27 count may include the audit scripts themselves."
echo "This gate therefore excludes audit-output and phase gate scripts."

REAL_OUTPUT_PATTERN_COUNT=$(
grep -REn \
'(echo|printf|print)[^#]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
.github scripts app \
--exclude='*.pyc' \
--exclude-dir='__pycache__' \
--exclude-dir='audit-output' \
--exclude='phase_p0_02_r*.sh' \
2>/dev/null | wc -l
)

echo "REAL_OUTPUT_PATTERN_COUNT=${REAL_OUTPUT_PATTERN_COUNT}"

if [ "${REAL_OUTPUT_PATTERN_COUNT}" -eq 0 ]; then
    pass "NO_NON_AUDIT_SECRET_OUTPUT_PATTERN"
else
    review "NON_AUDIT_SECRET_OUTPUT_PATTERN_PRESENT"
fi

echo
echo "============================================================"
echo "12. PREVIOUS REPORT RECONCILIATION"
echo "============================================================"

R27_REPORT="audit-output/p0_02_r27_secret_provenance_post_r26_integrity_gate.txt"
R28_REPORT="audit-output/p0_02_r28_secret_provenance_post_r27_regression_gate.txt"
R29_REPORT="audit-output/p0_02_r29_secret_provenance_cross_file_consistency_gate.txt"

for report in "${R27_REPORT}" "${R28_REPORT}" "${R29_REPORT}"; do
    if [ -f "${report}" ]; then
        pass "REPORT_PRESENT=${report}"
    else
        review "REPORT_MISSING=${report}"
    fi
done

echo
echo "============================================================"
echo "13. PREVIOUS R27 SECRET OUTPUT CLASSIFICATION"
echo "============================================================"

if [ -f "${R27_REPORT}" ]; then
    PREVIOUS_R27_OUTPUT_COUNT=$(
        awk -F= '/^SECRET_VALUE_OUTPUT_COUNT=/ {print $2; exit}' \
        "${R27_REPORT}" 2>/dev/null
    )

    echo "PREVIOUS_R27_SECRET_VALUE_OUTPUT_COUNT=${PREVIOUS_R27_OUTPUT_COUNT:-UNKNOWN}"

    if [ "${PREVIOUS_R27_OUTPUT_COUNT:-UNKNOWN}" = "2" ]; then
        review "R27_SECRET_OUTPUT_COUNT_REQUIRES_AUDIT_SELF_MATCH_RECONCILIATION"
    else
        pass "R27_SECRET_OUTPUT_COUNT_NOT_MATCHING_KNOWN_FALSE_POSITIVE=YES"
    fi
fi

echo
echo "============================================================"
echo "14. R29 LOGIC CONSISTENCY"
echo "============================================================"

if [ -f "${R29_REPORT}" ]; then

    R29_COMPOSE_MISSING_COUNT=$(
        grep -Ec \
        '^FAIL: COMPOSE_REFERENCE_MISSING=' \
        "${R29_REPORT}" 2>/dev/null || true
    )

    R29_INTERNAL_CONSISTENT=$(
        grep -Ec \
        '^PASS: R29_CROSS_FILE_SECRET_PROVENANCE_CONSISTENT$' \
        "${R29_REPORT}" 2>/dev/null || true
    )

    echo "R29_COMPOSE_MISSING_COUNT=${R29_COMPOSE_MISSING_COUNT}"
    echo "R29_INTERNAL_CONSISTENT_ASSERTION_COUNT=${R29_INTERNAL_CONSISTENT}"

    if [ "${R29_COMPOSE_MISSING_COUNT}" -gt 0 ] &&
       [ "${R29_INTERNAL_CONSISTENT}" -gt 0 ]; then
        review "R29_INTERNAL_CLASSIFICATION_CONTRADICTION_DETECTED"
    else
        pass "R29_INTERNAL_CLASSIFICATION_CONTRADICTION_NOT_DETECTED"
    fi
fi

echo
echo "============================================================"
echo "15. CURRENT STATE RECONCILIATION"
echo "============================================================"

if \
    [ "${ENV_SECRET_COUNT}" -eq 5 ] &&
    [ "${COMPOSE_TARGET_COUNT}" -eq 3 ] &&
    [ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] &&
    [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] &&
    [ "${RUNTIME_DIRECT_ASSIGNMENT_COUNT}" -eq 0 ] &&
    [ "${CI_IDENTIFIER_COUNT}" -eq 5 ]
then
    pass "CURRENT_SECRET_PROVENANCE_CORE_INVARIANTS_HOLD"
else
    fail "CURRENT_SECRET_PROVENANCE_CORE_INVARIANTS_BROKEN"
fi

echo
echo "============================================================"
echo "16. FINAL CLASSIFICATION"
echo "============================================================"

if [ "${FAILURE_COUNT}" -eq 0 ] && [ "${REVIEW_COUNT}" -eq 0 ]; then
    STATUS="CLEAN"
    RESULT="P0_02_R31_R26_R30_FORENSIC_RECONCILIATION_CLEAN"
    EXIT_CODE=0
elif [ "${FAILURE_COUNT}" -eq 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R31_R26_R30_FORENSIC_RECONCILIATION_REVIEW"
    EXIT_CODE=1
else
    STATUS="FAIL"
    RESULT="P0_02_R31_R26_R30_FORENSIC_RECONCILIATION_FAIL"
    EXIT_CODE=2
fi

echo "FAILURE_COUNT=${FAILURE_COUNT}"
echo "REVIEW_COUNT=${REVIEW_COUNT}"
echo "ENV_SECRET_AUTHORITY_COUNT=${ENV_SECRET_COUNT}"
echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "RUNTIME_DIRECT_ASSIGNMENT_COUNT=${RUNTIME_DIRECT_ASSIGNMENT_COUNT}"
echo "CI_IDENTIFIER_COUNT=${CI_IDENTIFIER_COUNT}"
echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"
echo "REAL_OUTPUT_PATTERN_COUNT=${REAL_OUTPUT_PATTERN_COUNT}"
echo "P0_02_R31_STATUS=${STATUS}"
echo "RESULT=${RESULT}"
echo "EXIT_CODE=${EXIT_CODE}"
echo "REPORT=${REPORT}"

exit "${EXIT_CODE}"
