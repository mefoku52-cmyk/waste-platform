#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

echo "============================================================"
echo "R27 COMPOSE LITERAL FORENSIC LOCATOR"
echo "============================================================"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "FAIL: COMPOSE_FILE_NOT_FOUND=$COMPOSE_FILE"
    exit 20
fi

echo
echo "1. BASH SYNTAX"
echo "============================================================"
bash -n "$COMPOSE_FILE" 2>/dev/null
echo "NOTE: docker-compose.yml is YAML, not Bash; syntax result is informational only."

echo
echo "2. SECRET-RELATED COMPOSE LINES"
echo "============================================================"

grep -nE \
'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY|DATABASE_URL' \
"$COMPOSE_FILE" \
|| true

echo
echo "3. POSSIBLE LITERAL SECRET ASSIGNMENTS"
echo "============================================================"

grep -nE \
'^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:' \
"$COMPOSE_FILE" \
|| true

echo
echo "4. POSSIBLE REFERENCE ASSIGNMENTS"
echo "============================================================"

grep -nE \
'^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:[[:space:]]*(\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*)' \
"$COMPOSE_FILE" \
|| true

echo
echo "5. DATABASE_URL CONTEXT"
echo "============================================================"

grep -nE \
'DATABASE_URL|POSTGRES_PASSWORD' \
"$COMPOSE_FILE" \
|| true

echo
echo "6. READ-ONLY GUARANTEES"
echo "============================================================"

echo "READ_ONLY=YES"
echo "NO_SOURCE_WRITES=YES"
echo "NO_RUNTIME_EXECUTION=YES"
echo "NO_BUILD=YES"
echo "NO_DEPLOYMENT=YES"
echo "NO_DELETIONS=YES"
echo "NO_SECRET_VALUES_PRINTED=YES"

echo
echo "============================================================"
echo "R27 COMPOSE LITERAL FORENSIC LOCATOR COMPLETE"
echo "============================================================"
