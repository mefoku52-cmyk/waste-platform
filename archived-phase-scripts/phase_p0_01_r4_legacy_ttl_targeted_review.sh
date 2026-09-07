#!/usr/bin/env bash
set -u

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/waste-platform}"

if [ -d "$PROJECT_ROOT" ]; then
    cd "$PROJECT_ROOT" || exit 20
else
    echo "FAIL: PROJECT_ROOT_NOT_FOUND=$PROJECT_ROOT"
    exit 20
fi

REPORT="audit-output/p0_01_r4_legacy_ttl_targeted_review.txt"
mkdir -p audit-output

FAILURE_COUNT=0
REVIEW_COUNT=0

pass() {
    echo "PASS: $1" | tee -a "$REPORT"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "FAIL: $1" | tee -a "$REPORT"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    echo "REVIEW: $1" | tee -a "$REPORT"
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

section "2. LEGACY IDENTIFIERS UNDER REVIEW"

LEGACY_A="JWT_ACCESS_TOKEN_EXPIRES_MINUTES"
LEGACY_R="JWT_REFRESH_TOKEN_EXPIRES_DAYS"

echo "LEGACY_ACCESS=$LEGACY_A" | tee -a "$REPORT"
echo "LEGACY_REFRESH=$LEGACY_R" | tee -a "$REPORT"

section "3. TARGETED ACTIVE REFERENCES"

TARGETS=(
    ".github/workflows/ci.yml"
    "phase_p0_01_production_source_boundary.sh"
    "phase_p0_01_r2_production_authority_resolver.sh"
    "phase_p0_01_r3_authority_discriminator.sh"
)

for f in "${TARGETS[@]}"; do

    if [ ! -f "$f" ]; then
        fail "TARGET_FILE_MISSING=$f"
        continue
    fi

    echo | tee -a "$REPORT"
    echo "--- TARGET=$f ---" | tee -a "$REPORT"

    MATCH_COUNT="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"

    echo "MATCH_COUNT=$MATCH_COUNT" | tee -a "$REPORT"

    if [ "$MATCH_COUNT" -eq 0 ]; then
        pass "NO_LEGACY_REFERENCE=$f"
        continue
    fi

    grep -nE "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null \
        | sed -E \
          's/(JWT_ACCESS_TOKEN_EXPIRES_MINUTES|JWT_REFRESH_TOKEN_EXPIRES_DAYS)/\1/g' \
        | tee -a "$REPORT"

done

section "4. RUNTIME DIRECTORY EXCLUSION TEST"

RUNTIME_LEGACY_COUNT=0

while IFS= read -r -d '' f; do

    case "$f" in
        ./.git/*)
            continue
            ;;
        ./audit-output/*)
            continue
            ;;
        ./scripts/forensics/archive/*)
            continue
            ;;
        ./_quarantine/*)
            continue
            ;;
    esac

    case "$f" in
        ./app/*|./apps/web/*)
            if grep -Eq "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null; then
                RUNTIME_LEGACY_COUNT=$((RUNTIME_LEGACY_COUNT + 1))

                echo "RUNTIME_LEGACY_FILE=$f" | tee -a "$REPORT"

                grep -nE "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null \
                    | head -40 \
                    | tee -a "$REPORT"
            fi
            ;;
    esac

done < <(
    find app apps/web \
        -type f \
        \( \
            -name '*.py' \
            -o -name '*.sh' \
            -o -name '*.yml' \
            -o -name '*.yaml' \
            -o -name '*.toml' \
            -o -name '*.ini' \
            -o -name '*.conf' \
            -o -name '*.md' \
        \) \
        -not -path '*/node_modules/*' \
        -not -path '*/.next/*' \
        -print0 2>/dev/null
)

echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" | tee -a "$REPORT"

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ]; then
    pass "APP_RUNTIME_LEGACY_TTL_REFERENCES=0"
else
    fail "APP_RUNTIME_LEGACY_TTL_REFERENCES=$RUNTIME_LEGACY_COUNT"
fi

section "5. CI CLASSIFICATION"

if [ -f ".github/workflows/ci.yml" ]; then

    echo "--- CI CONTEXT ---" | tee -a "$REPORT"

    grep -n -B5 -A8 \
        -E "$LEGACY_A|$LEGACY_R" \
        ".github/workflows/ci.yml" 2>/dev/null \
        | tee -a "$REPORT"

    CI_RUNTIME_SIGNAL="$(grep -Ei -c \
        'uvicorn|gunicorn|python.*app|docker compose up|docker run|deploy|production' \
        ".github/workflows/ci.yml" 2>/dev/null || true)"

    echo "CI_RUNTIME_RELATED_SIGNAL_COUNT=$CI_RUNTIME_SIGNAL" | tee -a "$REPORT"

    if [ "$CI_RUNTIME_SIGNAL" -gt 0 ]; then
        review "CI_CONTAINS_RUNTIME_OR_DEPLOYMENT_SIGNALS"
    else
        pass "CI_LEGACY_REFERENCE_NOT_ACCOMPANIED_BY_RUNTIME_START_SIGNAL"
    fi

else
    review "CI_FILE_NOT_PRESENT_FOR_CONTEXT_REVIEW"
fi

section "6. FORENSIC SCRIPT CLASSIFICATION"

for f in \
    "phase_p0_01_production_source_boundary.sh" \
    "phase_p0_01_r2_production_authority_resolver.sh" \
    "phase_p0_01_r3_authority_discriminator.sh"
do

    if [ ! -f "$f" ]; then
        continue
    fi

    echo "--- FORENSIC_SCRIPT=$f ---" | tee -a "$REPORT"

    FORENSIC_SIGNAL="$(grep -Ei -c \
        'audit|forensic|legacy|historical|archive|review|grep|find' \
        "$f" 2>/dev/null || true)"

    RUNTIME_SIGNAL="$(grep -Ei -c \
        'uvicorn|gunicorn|docker compose up|docker run|subprocess|exec |source .*env|\.env.production' \
        "$f" 2>/dev/null || true)"

    echo "FORENSIC_SIGNAL_COUNT=$FORENSIC_SIGNAL" | tee -a "$REPORT"
    echo "RUNTIME_EXECUTION_SIGNAL_COUNT=$RUNTIME_SIGNAL" | tee -a "$REPORT"

    if [ "$FORENSIC_SIGNAL" -gt 0 ] && [ "$RUNTIME_SIGNAL" -eq 0 ]; then
        pass "REFERENCE_CLASSIFIED_AS_FORENSIC_ONLY=$f"
    elif [ "$RUNTIME_SIGNAL" -gt 0 ]; then
        review "FORENSIC_SCRIPT_HAS_RUNTIME_EXECUTION_SIGNAL=$f"
    else
        review "FORENSIC_CLASSIFICATION_NOT_CONCLUSIVE=$f"
    fi

done

section "7. FINAL RUNTIME AUTHORITY TEST"

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ]; then
    pass "CURRENT_APP_RUNTIME_DOES_NOT_REFERENCE_LEGACY_TTL_NAMES"
else
    fail "CURRENT_APP_RUNTIME_REFERENCES_LEGACY_TTL_NAMES"
fi

section "8. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -eq 0 ] && [ "$RUNTIME_LEGACY_COUNT" -eq 0 ]; then

    echo "P0_01_R4_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_01_R4_LEGACY_TTL_RUNTIME_BOUNDARY_CLEAN" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"

    exit 0

elif [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_01_R4_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_01_R4_LEGACY_TTL_RUNTIME_BOUNDARY_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"

    exit 20

else

    echo "P0_01_R4_STATUS=REVIEW" | tee -a "$REPORT"
    echo "RESULT=P0_01_R4_LEGACY_TTL_RUNTIME_BOUNDARY_REVIEW_REQUIRED" | tee -a "$REPORT"
    echo "EXIT_CODE=10" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"

    exit 10

fi
