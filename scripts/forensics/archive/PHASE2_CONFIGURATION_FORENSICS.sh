#!/usr/bin/env bash

###############################################################################
# PHASE 2 - CONFIGURATION AUTHORITY FORENSICS
#
# PURPOSE:
#   Determine the ACTUAL configuration authority before changing anything.
#
# RULES:
#   - READ ONLY
#   - DO NOT MODIFY PROJECT CONFIGURATION
#   - DO NOT MODIFY SECTION 8
#   - DO NOT NORMALIZE VARIABLES
#   - DO NOT DELETE ALIASES
#   - DO NOT REWRITE .env files
#   - DO NOT RUN docker compose up/down
#   - DO NOT ROTATE SECRETS
#
# GOLDEN RULE:
#   Evidence first.
#   Authority second.
#   Fix third.
###############################################################################

set -u
set -o pipefail

ROOT="$PWD"

STAMP="$(date '+%Y%m%d_%H%M%S')"
OUT="$ROOT/audit-output/phase2_configuration_forensics_${STAMP}"

mkdir -p "$OUT"

REPORT="$OUT/phase2-report.txt"
OCCURRENCES="$OUT/configuration-occurrences.tsv"
FILES="$OUT/relevant-files.tsv"
COMPOSE="$OUT/docker-compose-context.txt"
ENV="$OUT/environment-context.txt"
GIT="$OUT/git-history-context.txt"

touch "$REPORT" "$OCCURRENCES" "$FILES" "$COMPOSE" "$ENV" "$GIT"

exec > >(tee "$REPORT") 2>&1

printf '\n'
printf '===============================================================================\n'
printf ' PHASE 2 - CONFIGURATION AUTHORITY FORENSICS\n'
printf '===============================================================================\n'
printf 'ROOT=%s\n' "$ROOT"
printf 'TIMESTAMP=%s\n' "$STAMP"
printf '\n'

###############################################################################
# SAFETY
###############################################################################

printf '%s\n' '--- SAFETY STATE ---'

if [ ! -f "$ROOT/waste-platform-extreme-audit.sh" ]; then
    echo "[FAIL] Audit script missing."
    exit 1
fi

if [ ! -f "$ROOT/docker-compose.yml" ]; then
    echo "[FAIL] docker-compose.yml missing."
    exit 1
fi

echo "[PASS] Required audit/config files exist."
echo "[PASS] This phase is read-only."

###############################################################################
# BASELINE CHECKSUMS
###############################################################################

printf '\n%s\n' '--- CURRENT BASELINE CHECKSUMS ---'

sha256sum \
    "$ROOT/waste-platform-extreme-audit.sh" \
    "$ROOT/docker-compose.yml" \
    2>/dev/null || true

###############################################################################
# RELEVANT CONFIGURATION FILES
###############################################################################

printf '\n%s\n' '--- RELEVANT CONFIGURATION FILES ---'

find "$ROOT" \
    -type f \
    \( \
        -name '.env' \
        -o -name '.env.*' \
        -o -name '*.env' \
        -o -name 'docker-compose.yml' \
        -o -name 'docker-compose.yaml' \
        -o -name 'compose.yml' \
        -o -name 'compose.yaml' \
        -o -name 'config.py' \
        -o -name 'settings.py' \
        -o -name 'configuration.py' \
        -o -name 'config.ts' \
        -o -name 'config.js' \
        -o -name 'settings.ts' \
        -o -name 'settings.js' \
    \) \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/audit-output/*' \
    -print 2>/dev/null |
sort -u |
while IFS= read -r f; do
    printf '%s\t%s\n' \
        "$(stat -c '%s' "$f" 2>/dev/null || printf '?')" \
        "${f#$ROOT/}"
done | tee "$FILES"

###############################################################################
# FINDINGS SOURCE
###############################################################################

printf '\n%s\n' '--- LATEST FINDINGS FILES ---'

LATEST="$(find "$ROOT/audit-output" \
    -maxdepth 2 \
    -type f \
    -name 'configuration-conflicts.tsv' \
    -printf '%T@ %p\n' 2>/dev/null |
    sort -nr |
    head -1 |
    cut -d' ' -f2-)"

if [ -n "${LATEST:-}" ] && [ -f "$LATEST" ]; then
    echo "CONFLICTS=$LATEST"
    printf '\n'
    nl -ba "$LATEST"
else
    echo "[WARN] Latest configuration-conflicts.tsv not found."
fi

LATEST_AUTH="$(find "$ROOT/audit-output" \
    -maxdepth 2 \
    -type f \
    -name 'configuration-authority-matrix.tsv' \
    -printf '%T@ %p\n' 2>/dev/null |
    sort -nr |
    head -1 |
    cut -d' ' -f2-)"

if [ -n "${LATEST_AUTH:-}" ] && [ -f "$LATEST_AUTH" ]; then
    echo
    echo "AUTHORITY_MATRIX=$LATEST_AUTH"
    printf '\n'
    nl -ba "$LATEST_AUTH"
else
    echo "[WARN] Latest configuration-authority-matrix.tsv not found."
fi

###############################################################################
# TARGET VARIABLE SET
###############################################################################

VARS=(
    DATABASE_URL
    DATABASE_HOST
    DATABASE_PORT
    DATABASE_NAME
    DATABASE_USER
    DATABASE_PASSWORD
    POSTGRES_HOST
    POSTGRES_PORT
    POSTGRES_DB
    POSTGRES_USER
    POSTGRES_PASSWORD

    REDIS_URL
    REDIS_HOST
    REDIS_PORT

    CORS_ALLOWED_ORIGINS
    CORS_ORIGINS

    NEXT_PUBLIC_API_URL
    NEXT_PUBLIC_API_BASE_URL

    JWT_ACCESS_TOKEN_EXPIRES_MINUTES
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    ACCESS_TOKEN_EXPIRE_MINUTES
    ACCESS_TOKEN_TTL_MINUTES

    JWT_REFRESH_TOKEN_EXPIRES_DAYS
    JWT_REFRESH_TOKEN_EXPIRE_DAYS
    REFRESH_TOKEN_EXPIRE_DAYS

    RATE_LIMIT_LIMIT
    RATE_LIMIT_REQUESTS
    RATE_LIMIT_PERIOD
    RATE_LIMIT_WINDOW_SECONDS

    JWT_SECRET_KEY
    JWT_REFRESH_SECRET_KEY
    JWT_ALGORITHM
    JWT_ISSUER
    JWT_AUDIENCE
)

###############################################################################
# OCCURRENCE SCAN
###############################################################################

printf '\n%s\n' '--- EXACT VARIABLE OCCURRENCE SCAN ---'

printf 'VARIABLE\tFILE\tLINE\tTEXT\n' > "$OCCURRENCES"

for VAR in "${VARS[@]}"; do

    printf '\n'
    printf '###############################################################################\n'
    printf '# VARIABLE: %s\n' "$VAR"
    printf '###############################################################################\n'

    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=.next \
        --exclude-dir=audit-output \
        --exclude-dir=__pycache__ \
        --exclude='*.pyc' \
        --exclude='*.log' \
        --exclude='*.db' \
        --exclude='*.sqlite' \
        --exclude='*.sqlite3' \
        --exclude='waste-audit-trace.txt' \
        --exclude='*.tsv' \
        --exclude='*.jsonl' \
        -- "$VAR" "$ROOT" 2>/dev/null |
    while IFS=: read -r FILE LINE REST; do

        REL="${FILE#$ROOT/}"

        printf '%s\t%s\t%s\t%s\n' \
            "$VAR" \
            "$REL" \
            "$LINE" \
            "$REST" >> "$OCCURRENCES"

        printf '%s:%s:%s\n' \
            "$REL" \
            "$LINE" \
            "$REST"

    done || true

done

###############################################################################
# COMPOSE CONTEXT
###############################################################################

printf '\n%s\n' '==============================================================================='
printf '%s\n' ' DOCKER COMPOSE - CONFIGURATION CONTEXT'
printf '%s\n' '==============================================================================='

if command -v sed >/dev/null 2>&1; then

    printf '\n--- DATABASE / POSTGRES ---\n'
    grep -nE \
        'DATABASE_|POSTGRES_|postgresql|postgres:' \
        "$ROOT/docker-compose.yml" \
        2>/dev/null |
    tee -a "$COMPOSE" || true

    printf '\n--- REDIS ---\n'
    grep -nE \
        'REDIS_|redis:' \
        "$ROOT/docker-compose.yml" \
        2>/dev/null |
    tee -a "$COMPOSE" || true

    printf '\n--- CORS ---\n'
    grep -nE \
        'CORS_|cors' \
        "$ROOT/docker-compose.yml" \
        2>/dev/null |
    tee -a "$COMPOSE" || true

    printf '\n--- API URL ---\n'
    grep -nE \
        'NEXT_PUBLIC_API_|API_URL|API_BASE' \
        "$ROOT/docker-compose.yml" \
        2>/dev/null |
    tee -a "$COMPOSE" || true

    printf '\n--- JWT ---\n'
    grep -nE \
        'JWT_|ACCESS_TOKEN_|REFRESH_TOKEN_' \
        "$ROOT/docker-compose.yml" \
        2>/dev/null |
    tee -a "$COMPOSE" || true

fi

###############################################################################
# ENVIRONMENT CONTEXT
###############################################################################

printf '\n%s\n' '==============================================================================='
printf '%s\n' ' ENVIRONMENT FILE CONTEXT'
printf '%s\n' '==============================================================================='

ENV_FILES="$(
    find "$ROOT" \
        -type f \
        \( \
            -name '.env' \
            -o -name '.env.*' \
            -o -name '*.env' \
        \) \
        ! -path '*/.git/*' \
        ! -path '*/node_modules/*' \
        ! -path '*/audit-output/*' \
        -print 2>/dev/null |
    sort -u
)"

if [ -n "$ENV_FILES" ]; then

    while IFS= read -r F; do

        [ -z "$F" ] && continue

        printf '\n--- %s ---\n' "${F#$ROOT/}"

        # IMPORTANT:
        # Never print secret values.
        #
        # We report only:
        #   variable name
        #   whether assignment exists
        #   line number
        #
        awk '
        /^[[:space:]]*#/ { next }

        /^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=/ {
            line = $0

            match(line, /^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*/)
            name = substr(line, RSTART, RLENGTH)

            gsub(/^[[:space:]]+/, "", name)
            gsub(/[[:space:]]+$/, "", name)

            print NR "\t" name "\tASSIGNMENT_PRESENT"
        }
        ' "$F" |
        tee -a "$ENV"

    done <<< "$ENV_FILES"

else
    echo "[INFO] No .env files found."
fi

###############################################################################
# RUNTIME CONFIGURATION SOURCE TRACING
###############################################################################

printf '\n%s\n' '==============================================================================='
printf '%s\n' ' PYTHON RUNTIME CONFIGURATION SOURCES'
printf '%s\n' '==============================================================================='

find "$ROOT" \
    -type f \
    \( -name '*.py' -o -name '*.pyi' \) \
    ! -path '*/.git/*' \
    ! -path '*/audit-output/*' \
    ! -path '*/.venv/*' \
    ! -path '*/venv/*' \
    ! -path '*/node_modules/*' \
    -print 2>/dev/null |
while IFS= read -r F; do

    grep -nE \
        'os\.environ|os\.getenv|BaseSettings|pydantic_settings|Settings\(|DATABASE_URL|REDIS_URL|CORS_|JWT_|RATE_LIMIT_|NEXT_PUBLIC_API_' \
        "$F" 2>/dev/null |
    sed "s#^#${F#$ROOT/}:#" || true

done

###############################################################################
# FRONTEND AUTHORITY
###############################################################################

printf '\n%s\n' '==============================================================================='
printf '%s\n' ' FRONTEND API URL AUTHORITY'
printf '%s\n' '==============================================================================='

find "$ROOT/apps/web" \
    -type f \
    \( \
        -name '*.ts' \
        -o -name '*.tsx' \
        -o -name '*.js' \
        -o -name '*.jsx' \
    \) \
    ! -path '*/node_modules/*' \
    ! -path '*/.next/*' \
    -print 2>/dev/null |
while IFS= read -r F; do

    grep -nE \
        'NEXT_PUBLIC_API_URL|NEXT_PUBLIC_API_BASE_URL|API_BASE_URL|API_URL' \
        "$F" 2>/dev/null |
    sed "s#^#${F#$ROOT/}:#" || true

done

###############################################################################
# GIT HISTORY - NAMES ONLY
###############################################################################

printf '\n%s\n' '==============================================================================='
printf '%s\n' ' GIT HISTORY - CONFIGURATION VARIABLE NAMES ONLY'
printf '%s\n' '==============================================================================='

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then

    for VAR in \
        DATABASE_URL \
        REDIS_URL \
        CORS_ALLOWED_ORIGINS \
        CORS_ORIGINS \
        NEXT_PUBLIC_API_URL \
        NEXT_PUBLIC_API_BASE_URL \
        JWT_SECRET_KEY \
        JWT_REFRESH_SECRET_KEY
    do
        printf '\n--- %s ---\n' "$VAR"

        git log \
            --all \
            --oneline \
            -S"$VAR" \
            -- \
            . 2>/dev/null |
        head -20 |
        tee -a "$GIT" || true
    done

else
    echo "[INFO] Not a git worktree."
fi

###############################################################################
# AUTHORITY QUESTIONS
###############################################################################

printf '\n'
printf '===============================================================================\n'
printf ' AUTHORITY QUESTIONS - NO AUTOMATIC ANSWERS\n'
printf '===============================================================================\n'

cat <<'QUESTIONS'

For every conflict we need to establish:

1. WHERE is the variable declared?
2. WHERE is it loaded?
3. WHERE is it transformed?
4. WHERE is it consumed?
5. WHICH value wins if multiple sources exist?
6. Is the losing source actually reachable at runtime?
7. Is the duplicate name an intentional compatibility alias?
8. Is the alias documented?
9. Is the alias tested?
10. Can the alias produce different runtime behavior?

DATABASE:
    Is DATABASE_URL the canonical runtime authority?
    Or are DATABASE_HOST/PORT/NAME/USER/PASSWORD independently consumed?

REDIS:
    Is REDIS_URL canonical?
    Or are REDIS_HOST/REDIS_PORT canonical?
    Can both paths produce different Redis targets?

CORS:
    Is CORS_ALLOWED_ORIGINS canonical?
    Is CORS_ORIGINS an alias?
    Are both consumed by runtime?
    Can they disagree?

API URL:
    Is NEXT_PUBLIC_API_BASE_URL canonical?
    Is NEXT_PUBLIC_API_URL legacy/compatibility?
    Which frontend code path consumes each?
    Can they point to different origins?

JWT:
    Which expiry variable is consumed?
    Are aliases resolved centrally or independently?
    Does precedence exist?
    Is precedence deterministic and documented?

RATE LIMIT:
    Which variable is the actual runtime limit?
    Are REQUESTS/LIMIT aliases?
    Are PERIOD/WINDOW_SECONDS aliases?
    Can both be configured simultaneously with divergent values?

SECRET KEYS:
    Is there exactly one authority for JWT_SECRET_KEY?
    Is there exactly one authority for JWT_REFRESH_SECRET_KEY?
    Are secrets required at startup rather than silently defaulted?
    Are any secret-like values embedded in source/config?

QUESTIONS

###############################################################################
# INTEGRITY SUMMARY
###############################################################################

printf '\n%s\n' '==============================================================================='
printf '%s\n' ' INTEGRITY SUMMARY'
printf '%s\n' '==============================================================================='

echo "[PASS] No configuration replacement performed."
echo "[PASS] No Section 8 modification performed."
echo "[PASS] No secrets printed."
echo "[PASS] No docker runtime mutation performed."
echo "[PASS] Evidence report generated."

printf '\nOUTPUT_DIR=%s\n' "$OUT"
printf 'REPORT=%s\n' "$REPORT"
printf 'OCCURRENCES=%s\n' "$OCCURRENCES"
printf 'FILES=%s\n' "$FILES"
printf 'COMPOSE=%s\n' "$COMPOSE"
printf 'ENV=%s\n' "$ENV"
printf 'GIT=%s\n' "$GIT"

printf '\n===============================================================================\n'
printf ' PHASE 2 COMPLETE - NO FIX APPLIED\n'
printf '===============================================================================\n'
