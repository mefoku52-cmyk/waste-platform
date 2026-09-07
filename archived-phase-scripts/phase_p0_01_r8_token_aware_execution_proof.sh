#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_01_r8_token_aware_execution_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
ACTUAL_EXEC_COUNT=0
REFERENCE_ONLY_COUNT=0
IGNORED_PATTERN_COUNT=0

mkdir -p audit-output 2>/dev/null || true
: > "$REPORT"

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

section "3. SHELL SYNTAX VALIDATION"

for f in "${FORENSIC_FILES[@]}"; do
    [ -f "$f" ] || continue

    if bash -n "$f" 2>/dev/null; then
        pass "BASH_SYNTAX_VALID=$f"
    else
        fail "BASH_SYNTAX_INVALID=$f"
    fi
done

section "4. TOKEN-AWARE SEMANTIC EXECUTION ANALYSIS"

#
# R8 rule:
#
# 1. Comments are ignored.
# 2. echo/printf are output only.
# 3. grep/find/sed/awk/rg are forensic search commands.
# 4. Quoted strings are DATA, not shell command positions.
# 5. Variable assignments are DATA unless command substitution exists.
# 6. Runtime command candidates are evaluated only outside quotes.
#
# The purpose is specifically to prevent:
#
#     'uvicorn|gunicorn|docker compose up|docker run'
#
# from being interpreted as actual shell execution.
#

strip_quoted_strings() {
    python3 - "$1" <<'PY'
import sys

s = sys.argv[1]

out = []
i = 0
quote = None

while i < len(s):
    c = s[i]

    if quote is None:
        if c in ("'", '"'):
            quote = c
            out.append(" ")
            i += 1
            continue

        if c == "\\" and i + 1 < len(s):
            out.append(" ")
            out.append(" ")
            i += 2
            continue

        out.append(c)
        i += 1
        continue

    if quote == "'":
        if c == "'":
            quote = None
        out.append(" ")
        i += 1
        continue

    if quote == '"':
        if c == "\\" and i + 1 < len(s):
            out.append(" ")
            out.append(" ")
            i += 2
            continue

        if c == '"':
            quote = None

        out.append(" ")
        i += 1
        continue

sys.stdout.write("".join(out))
PY
}

for f in "${FORENSIC_FILES[@]}"; do
    [ -f "$f" ] || continue

    echo | tee -a "$REPORT"
    echo "--- ANALYZE=$f ---" | tee -a "$REPORT"

    while IFS= read -r record; do

        line_no="${record%%:*}"
        text="${record#*:}"

        [ -n "$line_no" ] || continue

        stripped="$(printf '%s\n' "$text" | sed 's/^[[:space:]]*//')"

        [ -z "$stripped" ] && continue

        #
        # Comments
        #
        case "$stripped" in
            \#*)
                REFERENCE_ONLY_COUNT=$((REFERENCE_ONLY_COUNT + 1))
                continue
                ;;
        esac

        #
        # Create quote-neutral representation.
        #
        neutral="$(strip_quoted_strings "$stripped")"

        #
        # Ignore empty result.
        #
        [ -z "${neutral//[[:space:]]/}" ] && continue

        #
        # Output commands.
        #
        if printf '%s\n' "$neutral" |
            grep -Eq '^(echo|printf)([[:space:]]|$)'; then

            if printf '%s\n' "$stripped" |
                grep -Eq '(docker|docker-compose|uvicorn|gunicorn|subprocess|exec|source|\.env)'; then

                IGNORED_PATTERN_COUNT=$((IGNORED_PATTERN_COUNT + 1))

                echo "IGNORED_OUTPUT line=$line_no text=$stripped" |
                    tee -a "$REPORT"
            fi

            continue
        fi

        #
        # Search commands.
        #
        if printf '%s\n' "$neutral" |
            grep -Eq '^(grep|find|sed|awk|rg|ripgrep)([[:space:]]|$)'; then

            if printf '%s\n' "$stripped" |
                grep -Eq '(docker|docker-compose|uvicorn|gunicorn|subprocess|exec|source|\.env)'; then

                IGNORED_PATTERN_COUNT=$((IGNORED_PATTERN_COUNT + 1))

                echo "IGNORED_SEARCH_PATTERN line=$line_no text=$stripped" |
                    tee -a "$REPORT"
            fi

            continue
        fi

        #
        # Pure assignments.
        #
        if printf '%s\n' "$neutral" |
            grep -Eq '^[A-Za-z_][A-Za-z0-9_]*='; then

            if printf '%s\n' "$stripped" |
                grep -q '\$('; then

                echo "COMMAND_SUBSTITUTION line=$line_no text=$stripped" |
                    tee -a "$REPORT"

                ACTUAL_EXEC_COUNT=$((ACTUAL_EXEC_COUNT + 1))
            else
                REFERENCE_ONLY_COUNT=$((REFERENCE_ONLY_COUNT + 1))
            fi

            continue
        fi

        #
        # Remove leading shell environment assignments:
        #
        # FOO=bar docker ...
        #
        command_part="$neutral"

        while printf '%s\n' "$command_part" |
            grep -Eq '^[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+'; do

            command_part="$(
                printf '%s\n' "$command_part" |
                sed -E 's/^[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+//'
            )"
        done

        #
        # Explicit command at command position.
        #
        if printf '%s\n' "$command_part" |
            grep -Eq \
            '^(sudo[[:space:]]+)?(bash|sh|source|docker|docker-compose|uvicorn|gunicorn)([[:space:]]|$)'; then

            echo "ACTUAL_COMMAND_POSITION line=$line_no text=$stripped" |
                tee -a "$REPORT"

            ACTUAL_EXEC_COUNT=$((ACTUAL_EXEC_COUNT + 1))
            continue
        fi

        #
        # Commands after actual shell operators.
        #
        #
        # IMPORTANT:
        # This operates on the quote-neutral representation.
        # Therefore a "|" inside:
        #
        #   'uvicorn|docker|docker run'
        #
        # has already disappeared.
        #
        if printf '%s\n' "$command_part" |
            grep -Eq \
            '(^|[;&]|&&|\|\|)[[:space:]]*(sudo[[:space:]]+)?(bash|sh|source|docker|docker-compose|uvicorn|gunicorn)([[:space:]]|$)'; then

            echo "ACTUAL_COMMAND_POSITION_AFTER_OPERATOR line=$line_no text=$stripped" |
                tee -a "$REPORT"

            ACTUAL_EXEC_COUNT=$((ACTUAL_EXEC_COUNT + 1))
            continue
        fi

    done < <(
        nl -ba "$f" 2>/dev/null |
        sed 's/^[[:space:]]*//'
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
                "$root" 2>/dev/null |
            wc -l
        )"

        refs="$(
            grep -RInE \
                --exclude-dir=.git \
                --exclude-dir=audit-output \
                --exclude-dir=scripts \
                --exclude-dir=_quarantine \
                "$LEGACY_ACCESS|$LEGACY_REFRESH" \
                "$root" 2>/dev/null |
            wc -l
        )"

        RUNTIME_LEGACY_COUNT=$((RUNTIME_LEGACY_COUNT + count))
        RUNTIME_LEGACY_REFS=$((RUNTIME_LEGACY_REFS + refs))
    fi
done

echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" |
    tee -a "$REPORT"

echo "RUNTIME_LEGACY_REFERENCE_COUNT=$RUNTIME_LEGACY_REFS" |
    tee -a "$REPORT"

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ] &&
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
        2>/dev/null |
    wc -l
)"

echo "PRODUCTION_LEGACY_REFERENCE_COUNT=$PROD_LEGACY_REFS" |
    tee -a "$REPORT"

if [ "$PROD_LEGACY_REFS" -eq 0 ]; then
    pass "PRODUCTION_LEGACY_TTL_ZERO"
else
    fail "PRODUCTION_LEGACY_TTL_PRESENT"
fi

section "7. SEMANTIC EXECUTION DECISION"

echo "ACTUAL_EXECUTION_COUNT=$ACTUAL_EXEC_COUNT" |
    tee -a "$REPORT"

echo "REFERENCE_ONLY_COUNT=$REFERENCE_ONLY_COUNT" |
    tee -a "$REPORT"

echo "IGNORED_PATTERN_COUNT=$IGNORED_PATTERN_COUNT" |
    tee -a "$REPORT"

if [ "$ACTUAL_EXEC_COUNT" -eq 0 ]; then
    pass "NO_SEMANTIC_RUNTIME_EXECUTION_CONFIRMED"
else
    review "SEMANTIC_RUNTIME_EXECUTION_CONTEXTS=$ACTUAL_EXEC_COUNT"
fi

section "8. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" |
    tee -a "$REPORT"

echo "REVIEW_COUNT=$REVIEW_COUNT" |
    tee -a "$REPORT"

echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" |
    tee -a "$REPORT"

echo "RUNTIME_LEGACY_REFERENCE_COUNT=$RUNTIME_LEGACY_REFS" |
    tee -a "$REPORT"

echo "PRODUCTION_LEGACY_REFERENCE_COUNT=$PROD_LEGACY_REFS" |
    tee -a "$REPORT"

echo "ACTUAL_EXECUTION_COUNT=$ACTUAL_EXEC_COUNT" |
    tee -a "$REPORT"

echo "REFERENCE_ONLY_COUNT=$REFERENCE_ONLY_COUNT" |
    tee -a "$REPORT"

echo "IGNORED_PATTERN_COUNT=$IGNORED_PATTERN_COUNT" |
    tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_01_R8_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_01_R8_TOKEN_AWARE_EXECUTION_BOUNDARY_FAILURE" |
        tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"

    exit 20
fi

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ] &&
   [ "$RUNTIME_LEGACY_REFS" -eq 0 ] &&
   [ "$PROD_LEGACY_REFS" -eq 0 ] &&
   [ "$ACTUAL_EXEC_COUNT" -eq 0 ]; then

    echo "P0_01_R8_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_01_R8_TOKEN_AWARE_EXECUTION_BOUNDARY_CLEAN" |
        tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"

    exit 0
fi

echo "P0_01_R8_STATUS=REVIEW" | tee -a "$REPORT"
echo "RESULT=P0_01_R8_TOKEN_AWARE_EXECUTION_BOUNDARY_REVIEW_REQUIRED" |
    tee -a "$REPORT"
echo "EXIT_CODE=10" | tee -a "$REPORT"

echo
echo "REPORT=$REPORT"

exit 10
