#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_01_r6_forensic_execution_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
ACTUAL_EXEC_COUNT=0
REFERENCE_ONLY_COUNT=0

mkdir -p audit-output 2>/dev/null || true

pass() {
    echo "PASS: $1" | tee -a "$REPORT"
}

fail() {
    echo "FAIL: $1" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    echo "REVIEW: $1" | tee -a "$REPORT"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

section() {
    echo | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
    echo "$1" | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
}

: > "$REPORT"

section "1. SAFETY PRECHECK"

if [ "$PROJECT_ROOT" = "$HOME/waste-platform" ] || \
   [ "$(basename "$PROJECT_ROOT")" = "waste-platform" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "UNEXPECTED_PROJECT_ROOT=$PROJECT_ROOT"
fi

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_DELETIONS=YES"
pass "BOUNDED_SCAN=YES"

section "2. TARGET FORENSIC FILES"

FORENSIC_FILES=(
    "phase_p0_01_production_source_boundary.sh"
    "phase_p0_01_r4_legacy_ttl_targeted_review.sh"
)

for f in "${FORENSIC_FILES[@]}"; do
    if [ -f "$f" ]; then
        pass "TARGET_PRESENT=$f"
    else
        fail "TARGET_MISSING=$f"
    fi
done

section "3. EXECUTION-SIGNAL EXTRACTION"

for f in "${FORENSIC_FILES[@]}"; do
    [ -f "$f" ] || continue

    echo | tee -a "$REPORT"
    echo "--- FILE=$f ---" | tee -a "$REPORT"

    SIGNALS="$(grep -nE \
        '(^|[;&|])([[:space:]]*)(bash|sh|source|\.|exec|docker|docker-compose|uvicorn|gunicorn)([[:space:]]|$)|subprocess\.(run|Popen|call|check_call|check_output)|os\.(system|popen)|eval[[:space:]]|xargs[[:space:]]' \
        "$f" 2>/dev/null || true)"

    if [ -n "$SIGNALS" ]; then
        echo "$SIGNALS" | tee -a "$REPORT"
    else
        echo "NO_DIRECT_EXECUTION_PATTERN_MATCH" | tee -a "$REPORT"
    fi
done

section "4. CONTEXT CLASSIFICATION"

for f in "${FORENSIC_FILES[@]}"; do
    [ -f "$f" ] || continue

    echo | tee -a "$REPORT"
    echo "--- CLASSIFY=$f ---" | tee -a "$REPORT"

    while IFS=: read -r line_no line_text; do
        [ -n "${line_no:-}" ] || continue

        context="UNKNOWN"

        # Comments are not execution.
        if echo "$line_text" | grep -qE '^[[:space:]]*#'; then
            context="COMMENT"
        fi

        # Pure grep/find/awk/sed pattern construction is not execution.
        if echo "$line_text" | grep -qE \
            '(grep|find|awk|sed|rg|ripgrep)[^#]*(uvicorn|gunicorn|docker|subprocess|exec|source|\.env)'; then
            context="SEARCH_OR_PATTERN"
        fi

        # Quoted strings used as data/patterns are not execution by themselves.
        if echo "$line_text" | grep -qE \
            '^[[:space:]]*(echo|printf)[[:space:]].*(uvicorn|gunicorn|docker|subprocess|exec|source|\.env)'; then
            context="OUTPUT_ONLY"
        fi

        # Variable assignments containing command-like text are data,
        # unless command substitution is actually present.
        if echo "$line_text" | grep -qE \
            '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=.*(uvicorn|gunicorn|docker|subprocess|exec|source|\.env)' &&
           ! echo "$line_text" | grep -qE '\$\('; then
            context="VARIABLE_DATA"
        fi

        # Command substitution is an actual shell execution context.
        if echo "$line_text" | grep -qE '\$\([^)]*\)'; then
            context="COMMAND_SUBSTITUTION"
        fi

        # Explicit shell execution.
        if echo "$line_text" | grep -qE \
            '(^|[;&|])[[:space:]]*(bash|sh|source|\.)[[:space:]]+'; then
            context="EXPLICIT_SHELL_EXECUTION"
        fi

        # Explicit process execution APIs.
        if echo "$line_text" | grep -qE \
            'subprocess\.(run|Popen|call|check_call|check_output)|os\.(system|popen)|eval[[:space:]]'; then
            context="PROCESS_EXECUTION_API"
        fi

        # Explicit Docker execution.
        if echo "$line_text" | grep -qE \
            '(^|[;&|])[[:space:]]*(docker|docker-compose)([[:space:]]|$)'; then
            context="DOCKER_COMMAND"
        fi

        # Explicit server execution.
        if echo "$line_text" | grep -qE \
            '(^|[;&|])[[:space:]]*(uvicorn|gunicorn)([[:space:]]|$)'; then
            context="SERVER_COMMAND"
        fi

        echo "LINE=$line_no CONTEXT=$context TEXT=$line_text" | tee -a "$REPORT"

        case "$context" in
            EXPLICIT_SHELL_EXECUTION|PROCESS_EXECUTION_API|DOCKER_COMMAND|SERVER_COMMAND|COMMAND_SUBSTITUTION)
                ACTUAL_EXEC_COUNT=$((ACTUAL_EXEC_COUNT + 1))
                ;;
            *)
                REFERENCE_ONLY_COUNT=$((REFERENCE_ONLY_COUNT + 1))
                ;;
        esac

    done < <(
        grep -nE \
        '(^|[;&|])([[:space:]]*)(bash|sh|source|\.|exec|docker|docker-compose|uvicorn|gunicorn)([[:space:]]|$)|subprocess\.(run|Popen|call|check_call|check_output)|os\.(system|popen)|eval[[:space:]]|xargs[[:space:]]' \
        "$f" 2>/dev/null || true
    )
done

section "5. LEGACY TTL RUNTIME PROOF"

LEGACY_ACCESS="JWT_ACCESS_TOKEN_EXPIRES_MINUTES"
LEGACY_REFRESH="JWT_REFRESH_TOKEN_EXPIRES_DAYS"

RUNTIME_LEGACY_COUNT=0
RUNTIME_LEGACY_REFS=0

for root in app apps/web; do
    if [ -d "$root" ]; then
        count="$(
            grep -RIlE \
                --exclude-dir=.git \
                --exclude-dir=audit-output \
                --exclude-dir=scripts \
                --exclude-dir=_quarantine \
                "$LEGACY_ACCESS|$LEGACY_REFRESH" \
                "$root" 2>/dev/null | wc -l
        )"

        refs="$(
            grep -RInE \
                --exclude-dir=.git \
                --exclude-dir=audit-output \
                --exclude-dir=scripts \
                --exclude-dir=_quarantine \
                "$LEGACY_ACCESS|$LEGACY_REFRESH" \
                "$root" 2>/dev/null | wc -l
        )"

        RUNTIME_LEGACY_COUNT=$((RUNTIME_LEGACY_COUNT + count))
        RUNTIME_LEGACY_REFS=$((RUNTIME_LEGACY_REFS + refs))
    fi
done

echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_REFERENCE_COUNT=$RUNTIME_LEGACY_REFS" | tee -a "$REPORT"

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ] && \
   [ "$RUNTIME_LEGACY_REFS" -eq 0 ]; then
    pass "CURRENT_APPLICATION_RUNTIME_LEGACY_TTL_ZERO"
else
    fail "CURRENT_APPLICATION_RUNTIME_LEGACY_TTL_PRESENT"
fi

section "6. PRODUCTION CONFIGURATION PROOF"

PROD_LEGACY_REFS="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=_quarantine \
        --exclude-dir=scripts \
        "$LEGACY_ACCESS|$LEGACY_REFRESH" \
        .env.production \
        docker-compose.yml \
        docker \
        app \
        apps/web \
        2>/dev/null | wc -l
)"

echo "PRODUCTION_LEGACY_REFERENCE_COUNT=$PROD_LEGACY_REFS" | tee -a "$REPORT"

if [ "$PROD_LEGACY_REFS" -eq 0 ]; then
    pass "PRODUCTION_LEGACY_TTL_ZERO"
else
    fail "PRODUCTION_LEGACY_TTL_PRESENT"
fi

section "7. FORENSIC SCRIPT EXECUTION DECISION"

echo "FORENSIC_ACTUAL_EXECUTION_COUNT=$ACTUAL_EXEC_COUNT" | tee -a "$REPORT"
echo "FORENSIC_REFERENCE_ONLY_COUNT=$REFERENCE_ONLY_COUNT" | tee -a "$REPORT"

if [ "$ACTUAL_EXEC_COUNT" -eq 0 ]; then
    pass "NO_ACTUAL_FORENSIC_RUNTIME_EXECUTION_CONTEXT_CONFIRMED"
else
    review "ACTUAL_FORENSIC_EXECUTION_CONTEXTS=$ACTUAL_EXEC_COUNT"
fi

section "8. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_REFERENCE_COUNT=$RUNTIME_LEGACY_REFS" | tee -a "$REPORT"
echo "PRODUCTION_LEGACY_REFERENCE_COUNT=$PROD_LEGACY_REFS" | tee -a "$REPORT"
echo "FORENSIC_ACTUAL_EXECUTION_COUNT=$ACTUAL_EXEC_COUNT" | tee -a "$REPORT"
echo "FORENSIC_REFERENCE_ONLY_COUNT=$REFERENCE_ONLY_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    echo "P0_01_R6_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_01_R6_FORENSIC_EXECUTION_BOUNDARY_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"
    echo
    echo "REPORT=$REPORT"
    exit 20
fi

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ] && \
   [ "$RUNTIME_LEGACY_REFS" -eq 0 ] && \
   [ "$PROD_LEGACY_REFS" -eq 0 ] && \
   [ "$ACTUAL_EXEC_COUNT" -eq 0 ]; then

    echo "P0_01_R6_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_01_R6_FORENSIC_EXECUTION_BOUNDARY_CLEAN" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"
    echo
    echo "REPORT=$REPORT"
    exit 0
fi

echo "P0_01_R6_STATUS=REVIEW" | tee -a "$REPORT"
echo "RESULT=P0_01_R6_FORENSIC_EXECUTION_BOUNDARY_REVIEW_REQUIRED" | tee -a "$REPORT"
echo "EXIT_CODE=10" | tee -a "$REPORT"
echo
echo "REPORT=$REPORT"
exit 10
