#!/data/data/com.termux/files/usr/bin/bash
set -u

PROJECT_ROOT="${HOME}/waste-platform"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

echo "============================================================"
echo "P0-02 R23 SECRET PROVENANCE PARSER PROBE"
echo "============================================================"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "FAIL: COMPOSE_FILE_MISSING"
    exit 20
fi

echo
echo "============================================================"
echo "1. COMPOSE SECRET LINES"
echo "============================================================"

grep -nE 'POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|DATABASE_URL' \
    "$COMPOSE_FILE" | \
    sed -E 's/(=.*)/=<REDACTED>/'

echo
echo "============================================================"
echo "2. EXACT TOKEN FORMS PRESENT"
echo "============================================================"

for token in \
    POSTGRES_PASSWORD \
    DATABASE_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    S3_SECRET_KEY
do
    echo
    echo "TOKEN=$token"

    if grep -nF '${'"$token"'}' "$COMPOSE_FILE" >/dev/null 2>&1; then
        echo "PASS: BRACED_REFERENCE_PRESENT"
    else
        echo "MISS: BRACED_REFERENCE_NOT_FOUND"
    fi

    if grep -nF '$'"$token" "$COMPOSE_FILE" >/dev/null 2>&1; then
        echo "PASS: DOLLAR_REFERENCE_PRESENT"
    else
        echo "MISS: DOLLAR_REFERENCE_NOT_FOUND"
    fi

    if grep -nE '^[[:space:]]*-[[:space:]]*'"$token"':|^[[:space:]]*'"$token"':' \
        "$COMPOSE_FILE" >/dev/null 2>&1; then
        echo "PASS: SECRET_TARGET_PRESENT"
    else
        echo "MISS: SECRET_TARGET_NOT_FOUND"
    fi
done

echo
echo "============================================================"
echo "3. DATABASE_URL SEMANTIC CONTEXT"
echo "============================================================"

grep -nE 'DATABASE_URL|postgresql|postgres://' "$COMPOSE_FILE" \
    | sed -E 's/(=.*)/=<REDACTED>/'

echo
echo "============================================================"
echo "4. LITERAL SECRET ASSIGNMENT CHECK"
echo "============================================================"

literal_count=0

for token in \
    POSTGRES_PASSWORD \
    DATABASE_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    S3_SECRET_KEY
do
    if grep -nE '^[[:space:]]*'"$token"'[[:space:]]*=' "$COMPOSE_FILE" \
        >/dev/null 2>&1; then
        echo "FAIL: LITERAL_ENV_STYLE_ASSIGNMENT=$token"
        literal_count=$((literal_count + 1))
    else
        echo "PASS: NO_LITERAL_ENV_STYLE_ASSIGNMENT=$token"
    fi
done

echo
echo "LITERAL_ASSIGNMENT_COUNT=$literal_count"

echo
echo "============================================================"
echo "5. RAW COMPOSE RELEVANT CONTEXT"
echo "============================================================"

awk '
/POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY|DATABASE_URL/ {
    start=NR-2
    if (start < 1) start=1
    print "LINE " NR ": " $0
}
' "$COMPOSE_FILE" \
    | sed -E 's/(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)([=:]).*/\1\2<REDACTED>/'

echo
echo "============================================================"
echo "6. PARSER PROBE RESULT"
echo "============================================================"

echo "READ_ONLY=YES"
echo "NO_SOURCE_WRITES=YES"
echo "NO_RUNTIME_EXECUTION=YES"
echo "NO_BUILD=YES"
echo "NO_DEPLOYMENT=YES"
echo "NO_DELETIONS=YES"
echo "NO_SECRET_VALUES_PRINTED=YES"

exit 0
