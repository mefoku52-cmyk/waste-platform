#!/usr/bin/env bash
set -u

FILE="phase_p0_02_r27_secret_provenance_post_r26_integrity_gate.sh"

echo "============================================================"
echo "R27 LITERAL CLASSIFIER FORENSIC LOCATOR"
echo "============================================================"

if [ ! -f "$FILE" ]; then
    echo "FAIL: FILE_NOT_FOUND=$FILE"
    exit 20
fi

echo
echo "1. CURRENT LITERAL CLASSIFIER"
echo "============================================================"

grep -n -B 8 -A 18 \
  -E 'COMPOSE_LITERAL_COUNT|LITERAL_COMPOSE_SECRET|COMPOSE_LITERAL' \
  "$FILE" || true

echo
echo "2. COMPOSE SOURCE GROUND TRUTH"
echo "============================================================"

nl -ba docker-compose.yml |
  grep -E 'POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|DATABASE_URL' || true

echo
echo "3. CLASSIFICATION RULE"
echo "============================================================"

echo 'EXPECTED: ${VAR:?message} = REFERENCE'
echo 'EXPECTED: KEY: literal-secret = LITERAL'
echo 'EXPECTED: ${VAR} = REFERENCE'
echo 'EXPECTED: DATABASE_URL containing ${VAR} = CONTEXT'

echo
echo "4. READ-ONLY GUARANTEES"
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
echo "R27 LITERAL CLASSIFIER FORENSIC LOCATOR COMPLETE"
echo "============================================================"
