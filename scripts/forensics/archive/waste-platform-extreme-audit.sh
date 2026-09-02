#!/usr/bin/env bash

###############################################################################
# WASTE PLATFORM - EXTREME CONFIGURATION / AUTHORITY AUDIT
###############################################################################
#
# Goals:
#   ENV -> Pydantic config -> runtime settings -> consumer
#   Compose service scope
#   Frontend process.env usage
#   Configuration conflicts
#   Git history of VARIABLE NAMES only
#   Configuration Authority Matrix
#
# SECURITY:
#   Secret VALUES are never printed.
#   Git history checks VARIABLE NAMES, not secret values.
###############################################################################

set -u
set -o pipefail

###############################################################################
# 0. BOOTSTRAP
###############################################################################

ROOT="$(pwd)"

if [ ! -d "$ROOT" ]; then
    echo "[FATAL] Project directory does not exist: $ROOT"
    exit 1
fi

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
OUT_DIR="$ROOT/audit-output/$TIMESTAMP"

mkdir -p "$OUT_DIR" || {
    echo "[FATAL] Cannot create audit output directory:"
    echo "$OUT_DIR"
    exit 1
}

RAW="$OUT_DIR/raw-runtime-trace.txt"
COMPOSE="$OUT_DIR/compose-environment.tsv"
FRONT="$OUT_DIR/frontend-environment.tsv"
CONFLICT="$OUT_DIR/configuration-conflicts.tsv"
SECRET="$OUT_DIR/secret-key-history.tsv"
MATRIX="$OUT_DIR/configuration-authority-matrix.tsv"
MATRIX_VARS="$OUT_DIR/.matrix-vars.tmp"

touch "$RAW" "$COMPOSE" "$FRONT" "$CONFLICT" "$SECRET" "$MATRIX" || {
    echo "[FATAL] Cannot create audit output files."
    exit 1
}

###############################################################################
# 1. HELPERS
###############################################################################

section() {
    local TITLE="${1:-SECTION}"

    {
        echo
        echo "###############################################################################"
        echo "# $TITLE"
        echo "###############################################################################"
        echo
    } | tee -a "$RAW"
}

safe_grep() {
    grep "$@" 2>/dev/null || true
}

redact_env_file() {
    local FILE="$1"

    [ -f "$FILE" ] || return 0

    sed -E \
        -e 's/^([[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*[[:space:]]*)=.*/\1=[REDACTED]/' \
        "$FILE"
}

env_exists() {
    local VAR="$1"

    grep -hE \
        "^[[:space:]]*(export[[:space:]]+)?${VAR}[[:space:]]*=" \
        .env .env.* 2>/dev/null |
        grep -q . 
}

config_exists() {
    local VAR="$1"

    safe_grep -qE \
        "(^|[^A-Za-z0-9_])${VAR}([^A-Za-z0-9_]|$)" \
        app/core/config.py 2>/dev/null
}

runtime_exists() {
    local VAR="$1"

    safe_grep -RInqE \
        "(settings\.[A-Za-z_][A-Za-z0-9_]*|${VAR})" \
        app \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'
}

consumer_exists() {
    local VAR="$1"

    safe_grep -RInq \
        "$VAR" \
        app/shared \
        app/services \
        app/api \
        app/agents \
        app/infrastructure \
        app/modules \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'
}

compose_exists() {
    local VAR="$1"

    [ -f docker-compose.yml ] || return 1

    safe_grep -qE \
        "(\$\{${VAR}([}:,]|$)|[[:space:]]${VAR}[[:space:]]*:|[[:space:]]${VAR}[[:space:]]*=)" \
        docker-compose.yml
}

frontend_exists() {
    local VAR="$1"

    [ -d apps/web/src ] || return 1

    grep -RInqE \
        "process\.env\.${VAR}([^A-Za-z0-9_]|$)" \
        apps/web/src \
        --include='*.ts' \
        --include='*.tsx' \
        --include='*.js' \
        --include='*.jsx' \
        2>/dev/null
}

git_name_exists() {
    local VAR="$1"

    git rev-list --all --objects 2>/dev/null |
        grep -q "$VAR" && return 0

    git log \
        --all \
        --oneline \
        -S"$VAR" \
        -- . \
        2>/dev/null |
        grep -q .
}

default_exists() {
    local VAR="$1"

    safe_grep -qE \
        "${VAR}[[:space:]]*=|${VAR}[[:space:]]*:[^=]*Field[[:space:]]*\(" \
        app/core/config.py 2>/dev/null
}

###############################################################################
# 2. PROJECT CONTEXT
###############################################################################

section "1. PROJECT CONTEXT"

echo "PROJECT_ROOT=$ROOT"
echo "AUDIT_TIMESTAMP=$TIMESTAMP"
echo "OUTPUT_DIR=$OUT_DIR"
echo "SCRIPT=$ROOT/waste-platform-extreme-audit.sh"

echo
echo "Git:"
git rev-parse --show-toplevel 2>/dev/null || echo "Not a Git repository"

echo
echo "Python:"
python3 --version 2>/dev/null || true

echo
echo "Bash:"
bash --version 2>/dev/null | head -n1 || true

###############################################################################
# 3. ENVIRONMENT FILE INVENTORY
###############################################################################

section "2. ENVIRONMENT FILE INVENTORY"

for FILE in .env .env.*; do
    [ -f "$FILE" ] || continue

    echo
    echo "--- $FILE ---"
    redact_env_file "$FILE"
done

###############################################################################
# 4. CONFIGURATION FILE INVENTORY
###############################################################################

section "3. CONFIGURATION FILES"

for FILE in \
    app/core/config.py \
    docker-compose.yml \
    .env \
    .env.example \
    .env.local \
    .env.production \
    .env.development
do
    if [ -f "$FILE" ]; then
        echo "FOUND $FILE"
    else
        echo "ABSENT $FILE"
    fi
done

###############################################################################
# 5. BASIC ENV NAME INVENTORY
###############################################################################

section "4. ENVIRONMENT VARIABLE NAMES"

{
    for FILE in .env .env.*; do
        [ -f "$FILE" ] || continue

        sed -nE \
            's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=.*/\2/p' \
            "$FILE"
    done
} 2>/dev/null |
sort -u |
tee -a "$RAW"

###############################################################################
# 5B. CONFIG DECLARATION INVENTORY
###############################################################################

section "5. CONFIG DECLARATIONS"

if [ -f app/core/config.py ]; then
    safe_grep -nE \
        '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*[:=]|Field[[:space:]]*\(' \
        app/core/config.py |
        tee -a "$RAW"
else
    echo "app/core/config.py not found" | tee -a "$RAW"
fi

###############################################################################
# 6. SETTINGS RUNTIME TRACE
###############################################################################

section "6. SETTINGS.* RUNTIME TRACE"

safe_grep -RInE \
    'settings\.[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*' \
    app \
    --include='*.py' \
    --exclude='*.bak*' \
    --exclude-dir='__pycache__' |
tee -a "$RAW"

###############################################################################
# 7. IMPORTANT NESTED SETTINGS
###############################################################################

section "7. IMPORTANT NESTED SETTINGS"

for PATTERN in \
    'settings\.jwt\.' \
    'settings\.redis\.' \
    'settings\.rate_limit\.' \
    'settings\.email\.' \
    'settings\.database\.' \
    'settings\.frontend_url' \
    'settings\.is_development'
do
    echo
    echo "--- $PATTERN ---"

    safe_grep -RInE \
        "$PATTERN" \
        app \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'
done

###############################################################################
# 8. DOCKER COMPOSE SERVICE-SCOPED ENVIRONMENT
###############################################################################

section "8. DOCKER COMPOSE API ENVIRONMENT"

printf 'SERVICE\tKEY\tVALUE_REFERENCE\tLINE\n' > "$COMPOSE"

if [ -f docker-compose.yml ]; then

    awk '
function indent(s) {
    match(s, /^[[:space:]]*/)
    return RLENGTH
}

BEGIN {
    in_services = 0
    service = ""
}

/^[[:space:]]*services:[[:space:]]*$/ {
    in_services = 1
    service = ""
    next
}

in_services {
    n = indent($0)

    if (n == 2 && $0 ~ /^[[:space:]]*[A-Za-z0-9_-]+:[[:space:]]*$/) {
        service = $1
        sub(/:$/, "", service)
        next
    }

    if (n < 2 && $0 !~ /^[[:space:]]*$/) {
        service = ""
    }

    if (service != "" && n == 4 && $0 ~ /^[[:space:]]*[A-Za-z_][A-Za-z0-9_-]*:/) {
        key = $1
        sub(/:$/, "", key)

        if (service == "api" || service == "web" || service == "postgres" || service == "redis") {
            print service "\t" key "\t" $0 "\t" NR
        }
    }

    line = $0

    while (match(line, /\$\{[A-Za-z_][A-Za-z0-9_]*/)) {
        x = substr(line, RSTART, RLENGTH)
        sub(/^\$\{/, "", x)

        print "INTERPOLATION\t" x "\t" $0 "\t" NR

        line = substr(line, RSTART + RLENGTH)
    }
}
' docker-compose.yml |
    sort -u |
    tee -a "$COMPOSE"

else
    echo "docker-compose.yml not found" | tee -a "$COMPOSE"
fi

###############################################################################
# 9. FRONTEND LIVE ENVIRONMENT
###############################################################################

section "9. FRONTEND LIVE ENVIRONMENT"

printf 'VARIABLE\tSOURCE\tLINE\n' > "$FRONT"

if [ -d apps/web/src ]; then

    grep -RInE \
        'process\.env\.[A-Za-z_][A-Za-z0-9_]*' \
        apps/web/src \
        --include='*.ts' \
        --include='*.tsx' \
        --include='*.js' \
        --include='*.jsx' \
        2>/dev/null |
    grep -vE \
        '\.bak\.|\.backup\.|\.next/|node_modules/' |
    while IFS=: read -r FILE LINE REST; do

        VAR="$(
            printf '%s\n' "$REST" |
            sed -nE \
                's/.*process\.env\.([A-Za-z_][A-Za-z0-9_]*).*/\1/p' |
            head -n1
        )"

        if [ -n "${VAR:-}" ]; then
            printf '%s\t%s\t%s\n' \
                "$VAR" \
                "$FILE" \
                "$LINE"
        fi

    done |
    sort -u |
    tee -a "$FRONT"

else
    echo "apps/web/src not found" | tee -a "$FRONT"
fi

###############################################################################
# 10. API URL CONFLICT
###############################################################################

section "10. API URL CONFLICT"

if grep -q $'^NEXT_PUBLIC_API_URL\t' "$FRONT" &&
   grep -q $'^NEXT_PUBLIC_API_BASE_URL\t' "$FRONT"
then

    echo "REAL_CONFLICT"

    printf '%s\n' \
        $'NEXT_PUBLIC_API_URL\tNEXT_PUBLIC_API_BASE_URL\tLIVE/LIVE\tYES\tYES' |
        tee -a "$CONFLICT"

    echo
    echo "NEXT_PUBLIC_API_URL live references:"
    grep $'^NEXT_PUBLIC_API_URL\t' "$FRONT" || true

    echo
    echo "NEXT_PUBLIC_API_BASE_URL live references:"
    grep $'^NEXT_PUBLIC_API_BASE_URL\t' "$FRONT" || true

else
    echo "No simultaneous live frontend API variable usage detected."
fi

###############################################################################
# 11. CORS AUTHORITY CHECK
###############################################################################

section "11. CORS AUTHORITY CHECK"

echo "Pydantic:"
safe_grep -nE \
    'CORS_ORIGINS|CORS_ALLOWED_ORIGINS' \
    app/core/config.py

echo
echo "Compose:"
safe_grep -nE \
    'CORS_ORIGINS|CORS_ALLOWED_ORIGINS' \
    docker-compose.yml

echo
echo "Backend runtime:"
safe_grep -RInE \
    'settings\.CORS_ORIGINS|CORS_ALLOWED_ORIGINS|CORS_ORIGINS' \
    app \
    --include='*.py' \
    --exclude='*.bak*' \
    --exclude-dir='__pycache__'

###############################################################################
# 12. JWT AUTHORITY CHECK
###############################################################################

section "12. JWT AUTHORITY CHECK"

for VAR in \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    JWT_ALGORITHM \
    ACCESS_TOKEN_EXPIRE_MINUTES \
    REFRESH_TOKEN_EXPIRE_DAYS \
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES \
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES \
    JWT_REFRESH_TOKEN_EXPIRE_DAYS \
    JWT_REFRESH_TOKEN_EXPIRES_DAYS \
    ACCESS_TOKEN_TTL_MINUTES \
    JWT_ISSUER \
    JWT_AUDIENCE
do

    echo
    echo "--- $VAR ---"

    echo "ENV:"
    grep -hE \
        "^[[:space:]]*(export[[:space:]]+)?${VAR}[[:space:]]*=" \
        .env .env.* 2>/dev/null |
    sed -E 's/=.*$/=[REDACTED]/' || true

    echo "CONFIG:"
    safe_grep -nE \
        "(^|[^A-Za-z0-9_])${VAR}([^A-Za-z0-9_]|$)" \
        app/core/config.py

    echo "CODE:"
    safe_grep -RIn \
        "$VAR" \
        app \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'

done

###############################################################################
# 13. EMAIL AUTHORITY
###############################################################################

section "13. EMAIL AUTHORITY CHECK"

for VAR in \
    EMAIL_PROVIDER \
    EMAIL_FROM \
    SMTP_HOST \
    SMTP_PORT \
    SMTP_USERNAME \
    SMTP_PASSWORD \
    SMTP_USE_TLS \
    EMAIL_SMTP_HOST \
    EMAIL_SMTP_PORT \
    EMAIL_SMTP_USER \
    EMAIL_SMTP_PASSWORD \
    EMAIL_TLS \
    MAIL_SMTP_PASSWORD
do

    echo
    echo "--- $VAR ---"

    echo "ENV:"
    grep -hE \
        "^[[:space:]]*(export[[:space:]]+)?${VAR}[[:space:]]*=" \
        .env .env.* 2>/dev/null |
    sed -E 's/=.*$/=[REDACTED]/' || true

    echo "CONFIG:"
    safe_grep -nE \
        "(^|[^A-Za-z0-9_])${VAR}([^A-Za-z0-9_]|$)" \
        app/core/config.py

    echo "RUNTIME:"
    safe_grep -RInE \
        "settings\.email|${VAR}" \
        app/shared/infrastructure/email \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'

done

###############################################################################
# 14. REDIS / RATE LIMIT
###############################################################################

section "14. REDIS / RATE LIMIT AUTHORITY"

for VAR in \
    REDIS_HOST \
    REDIS_PORT \
    REDIS_URL \
    RATE_LIMIT_ENABLED \
    RATE_LIMIT_REQUESTS \
    RATE_LIMIT_PERIOD \
    RATE_LIMIT_LIMIT \
    RATE_LIMIT_WINDOW_SECONDS
do

    echo
    echo "--- $VAR ---"

    echo "ENV:"
    grep -hE \
        "^[[:space:]]*(export[[:space:]]+)?${VAR}[[:space:]]*=" \
        .env .env.* 2>/dev/null |
    sed -E 's/=.*$/=[REDACTED]/' || true

    echo "CONFIG:"
    safe_grep -nE \
        "(^|[^A-Za-z0-9_])${VAR}([^A-Za-z0-9_]|$)" \
        app/core/config.py

    echo "RUNTIME:"
    safe_grep -RInE \
        "settings\.redis|settings\.rate_limit|${VAR}" \
        app \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'

done

###############################################################################
# 15. DATABASE AUTHORITY
###############################################################################

section "15. DATABASE AUTHORITY"

for VAR in \
    DATABASE_URL \
    DATABASE_HOST \
    DATABASE_PORT \
    DATABASE_NAME \
    DATABASE_USER \
    DATABASE_PASSWORD \
    POSTGRES_HOST \
    POSTGRES_PORT \
    POSTGRES_DB \
    POSTGRES_USER \
    POSTGRES_PASSWORD
do

    echo
    echo "--- $VAR ---"

    echo "ENV:"
    grep -hE \
        "^[[:space:]]*(export[[:space:]]+)?${VAR}[[:space:]]*=" \
        .env .env.* 2>/dev/null |
    sed -E 's/=.*$/=[REDACTED]/' || true

    echo "CONFIG:"
    safe_grep -nE \
        "(^|[^A-Za-z0-9_])${VAR}([^A-Za-z0-9_]|$)" \
        app/core/config.py

    echo "COMPOSE:"
    safe_grep -nE \
        "(^|[^A-Za-z0-9_])${VAR}([^A-Za-z0-9_]|$)" \
        docker-compose.yml

    echo "CODE:"
    safe_grep -RIn \
        "$VAR" \
        app \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'

done

###############################################################################
# 16. S3 / MINIO
###############################################################################

section "16. S3 / MINIO AUTHORITY"

for VAR in \
    S3_ENDPOINT_URL \
    S3_PUBLIC_ENDPOINT_URL \
    S3_REGION \
    S3_ACCESS_KEY \
    S3_SECRET_KEY \
    S3_BUCKET_NAME \
    S3_BUCKET_DOCUMENTS \
    S3_BUCKET_MEDIA \
    S3_USE_SSL \
    S3_FORCE_PATH_STYLE \
    MINIO_ENDPOINT \
    MINIO_ROOT_USER \
    MINIO_ROOT_PASSWORD \
    MINIO_SECURE
do

    echo
    echo "--- $VAR ---"

    echo "ENV:"
    grep -hE \
        "^[[:space:]]*(export[[:space:]]+)?${VAR}[[:space:]]*=" \
        .env .env.* 2>/dev/null |
    sed -E 's/=.*$/=[REDACTED]/' || true

    echo "CONFIG:"
    safe_grep -nE \
        "(^|[^A-Za-z0-9_])${VAR}([^A-Za-z0-9_]|$)" \
        app/core/config.py

    echo "CODE:"
    safe_grep -RIn \
        "$VAR" \
        app \
        --include='*.py' \
        --exclude='*.bak*' \
        --exclude-dir='__pycache__'

done

###############################################################################
# 17. SECRET KEY NAME HISTORY
###############################################################################

section "17. SECRET KEY NAME HISTORY"

printf 'VARIABLE\tGIT_COMMITS_WITH_VARIABLE_NAME\tVALUE_PRINTED\n' > "$SECRET"

SECRET_VARS="
DATABASE_PASSWORD
POSTGRES_PASSWORD
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
S3_SECRET_KEY
SMTP_PASSWORD
EMAIL_SMTP_PASSWORD
GOOGLE_CLIENT_SECRET
MINIO_ROOT_PASSWORD
GRAFANA_PASSWORD
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
"

for VAR in $SECRET_VARS; do

    COUNT="$(
        git log \
            --all \
            --oneline \
            -S"$VAR" \
            -- . \
            2>/dev/null |
        wc -l |
        tr -d ' '
    )"

    printf '%s\t%s\tNO\n' \
        "$VAR" \
        "${COUNT:-0}" |
        tee -a "$SECRET"

done

echo
echo "IMPORTANT:"
echo "Git history checks VARIABLE NAMES."
echo "Secret VALUES are never printed."
echo "A positive count does NOT prove that a secret value was committed."

###############################################################################
# 18. CONFIGURATION AUTHORITY MATRIX
###############################################################################

section "18. CONFIGURATION AUTHORITY MATRIX"

printf \
    'VARIABLE\tENV\tCONFIG\tCOMPOSE\tRUNTIME\tCONSUMER\tFRONTEND\tGIT_HISTORY\tDEFAULT\tCONFLICT\tSTATUS\n' \
    > "$MATRIX"

###############################################################################
# Build variable universe
###############################################################################

{
    # ENV names
    for FILE in .env .env.*; do
        [ -f "$FILE" ] || continue

        sed -nE \
            's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=.*/\2/p' \
            "$FILE"
    done

    # Config identifiers
    if [ -f app/core/config.py ]; then
        grep -oE \
            '\b[A-Z][A-Z0-9_]{2,}\b' \
            app/core/config.py 2>/dev/null || true
    fi

    # Compose interpolation variables
    if [ -f docker-compose.yml ]; then
        grep -oE \
            '\$\{[A-Za-z_][A-Za-z0-9_]*' \
            docker-compose.yml 2>/dev/null |
        sed 's/^\${//'
    fi

    # Frontend process.env variables
    if [ -d apps/web/src ]; then
        grep -RhoE \
            'process\.env\.[A-Za-z_][A-Za-z0-9_]*' \
            apps/web/src \
            --include='*.ts' \
            --include='*.tsx' \
            --include='*.js' \
            --include='*.jsx' \
            2>/dev/null |
        sed 's/^process\.env\.//'
    fi

    # Known audit variables
    printf '%s\n' \
        JWT_SECRET_KEY \
        JWT_REFRESH_SECRET_KEY \
        JWT_ALGORITHM \
        ACCESS_TOKEN_EXPIRE_MINUTES \
        REFRESH_TOKEN_EXPIRE_DAYS \
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES \
        JWT_ACCESS_TOKEN_EXPIRES_MINUTES \
        JWT_REFRESH_TOKEN_EXPIRE_DAYS \
        JWT_REFRESH_TOKEN_EXPIRES_DAYS \
        ACCESS_TOKEN_TTL_MINUTES \
        JWT_ISSUER \
        JWT_AUDIENCE \
        CORS_ORIGINS \
        CORS_ALLOWED_ORIGINS \
        EMAIL_PROVIDER \
        EMAIL_FROM \
        SMTP_HOST \
        SMTP_PORT \
        SMTP_USERNAME \
        SMTP_PASSWORD \
        SMTP_USE_TLS \
        EMAIL_SMTP_HOST \
        EMAIL_SMTP_PORT \
        EMAIL_SMTP_USER \
        EMAIL_SMTP_PASSWORD \
        EMAIL_TLS \
        MAIL_SMTP_PASSWORD \
        REDIS_HOST \
        REDIS_PORT \
        REDIS_URL \
        RATE_LIMIT_ENABLED \
        RATE_LIMIT_REQUESTS \
        RATE_LIMIT_PERIOD \
        RATE_LIMIT_LIMIT \
        RATE_LIMIT_WINDOW_SECONDS \
        DATABASE_URL \
        DATABASE_HOST \
        DATABASE_PORT \
        DATABASE_NAME \
        DATABASE_USER \
        DATABASE_PASSWORD \
        POSTGRES_HOST \
        POSTGRES_PORT \
        POSTGRES_DB \
        POSTGRES_USER \
        POSTGRES_PASSWORD \
        S3_ENDPOINT_URL \
        S3_PUBLIC_ENDPOINT_URL \
        S3_REGION \
        S3_ACCESS_KEY \
        S3_SECRET_KEY \
        S3_BUCKET_NAME \
        S3_BUCKET_DOCUMENTS \
        S3_BUCKET_MEDIA \
        S3_USE_SSL \
        S3_FORCE_PATH_STYLE \
        MINIO_ENDPOINT \
        MINIO_ROOT_USER \
        MINIO_ROOT_PASSWORD \
        MINIO_SECURE \
        NEXT_PUBLIC_API_URL \
        NEXT_PUBLIC_API_BASE_URL \
        NEXT_PUBLIC_GOOGLE_CLIENT_ID

} |
grep -E '^[A-Za-z_][A-Za-z0-9_]*$' |
sort -u |
tee "$MATRIX_VARS" >/dev/null

###############################################################################
# Matrix evaluation
###############################################################################

while IFS= read -r VAR; do

    [ -n "$VAR" ] || continue

    ENV_STATUS="NO"
    CONFIG_STATUS="NO"
    COMPOSE_STATUS="NO"
    RUNTIME_STATUS="NO"
    CONSUMER_STATUS="NO"
    FRONTEND_STATUS="NO"
    GIT_STATUS="NO"
    DEFAULT_STATUS="NO"
    CONFLICT_STATUS="NO"
    STATUS="UNREFERENCED"

    if env_exists "$VAR"; then
        ENV_STATUS="YES"
    fi

    if config_exists "$VAR"; then
        CONFIG_STATUS="YES"
    fi

    if compose_exists "$VAR"; then
        COMPOSE_STATUS="YES"
    fi

    if runtime_exists "$VAR"; then
        RUNTIME_STATUS="YES"
    fi

    if consumer_exists "$VAR"; then
        CONSUMER_STATUS="YES"
    fi

    if frontend_exists "$VAR"; then
        FRONTEND_STATUS="YES"
    fi

    if git_name_exists "$VAR"; then
        GIT_STATUS="YES"
    fi

    if default_exists "$VAR"; then
        DEFAULT_STATUS="PRESENT_OR_DECLARED"
    fi

    ###########################################################################
    # Conflict detection
    ###########################################################################

    case "$VAR" in

        NEXT_PUBLIC_API_URL|NEXT_PUBLIC_API_BASE_URL)

            if grep -q $'^NEXT_PUBLIC_API_URL\t' "$FRONT" &&
               grep -q $'^NEXT_PUBLIC_API_BASE_URL\t' "$FRONT"
            then
                CONFLICT_STATUS="API_URL_ALIAS_CONFLICT"
            fi
            ;;

        CORS_ORIGINS|CORS_ALLOWED_ORIGINS)

            if safe_grep -q 'CORS_ORIGINS' app/core/config.py &&
               safe_grep -q 'CORS_ALLOWED_ORIGINS' app/core/config.py
            then
                CONFLICT_STATUS="CORS_DUAL_NAME"
            fi
            ;;

        DATABASE_URL)

            if safe_grep -q 'DATABASE_URL' app/core/config.py &&
               safe_grep -q 'POSTGRES_HOST' app/core/config.py
            then
                CONFLICT_STATUS="DATABASE_DUAL_MODEL"
            fi
            ;;

        JWT_ACCESS_TOKEN_EXPIRE_MINUTES|JWT_ACCESS_TOKEN_EXPIRES_MINUTES)

            if safe_grep -q \
                'JWT_ACCESS_TOKEN_EXPIRE_MINUTES' \
                app/core/config.py &&
               safe_grep -q \
                'JWT_ACCESS_TOKEN_EXPIRES_MINUTES' \
                app/core/config.py
            then
                CONFLICT_STATUS="JWT_EXPIRY_ALIAS_CONFLICT"
            fi
            ;;

        JWT_REFRESH_TOKEN_EXPIRE_DAYS|JWT_REFRESH_TOKEN_EXPIRES_DAYS)

            if safe_grep -q \
                'JWT_REFRESH_TOKEN_EXPIRE_DAYS' \
                app/core/config.py &&
               safe_grep -q \
                'JWT_REFRESH_TOKEN_EXPIRES_DAYS' \
                app/core/config.py
            then
                CONFLICT_STATUS="JWT_REFRESH_ALIAS_CONFLICT"
            fi
            ;;

        REDIS_URL)

            if safe_grep -q 'settings\.redis\.url' app &&
               (
                   safe_grep -q 'REDIS_HOST' app/core/config.py ||
                   safe_grep -q 'REDIS_PORT' app/core/config.py
               )
            then
                CONFLICT_STATUS="REDIS_URL_VS_HOST_PORT"
            fi
            ;;

        RATE_LIMIT_REQUESTS)

            if safe_grep -q 'RATE_LIMIT_REQUESTS' app/core/config.py &&
               safe_grep -q 'RATE_LIMIT_LIMIT' app/core/config.py
            then
                CONFLICT_STATUS="RATE_LIMIT_DUAL_LIMIT_NAME"
            fi
            ;;

    esac

    ###########################################################################
    # Derived status
    ###########################################################################

    if [ "$CONFLICT_STATUS" != "NO" ]; then

        STATUS="CONFLICT:$CONFLICT_STATUS"

    elif [ "$ENV_STATUS" = "YES" ] &&
         [ "$CONFIG_STATUS" = "YES" ] &&
         [ "$RUNTIME_STATUS" = "YES" ] &&
         [ "$CONSUMER_STATUS" = "YES" ]
    then

        STATUS="CONNECTED"

    elif [ "$ENV_STATUS" = "YES" ] &&
         [ "$CONFIG_STATUS" = "YES" ] &&
         [ "$RUNTIME_STATUS" = "YES" ]
    then

        STATUS="RUNTIME_CONNECTED_NO_CONSUMER_CONFIRMED"

    elif [ "$ENV_STATUS" = "YES" ] &&
         [ "$CONFIG_STATUS" = "YES" ]
    then

        STATUS="CONFIGURED_NOT_CONFIRMED_RUNTIME"

    elif [ "$CONFIG_STATUS" = "YES" ] &&
         [ "$RUNTIME_STATUS" = "YES" ]
    then

        STATUS="RUNTIME_CONFIG_WITHOUT_ENV"

    elif [ "$COMPOSE_STATUS" = "YES" ]; then

        STATUS="COMPOSE_ONLY"

    elif [ "$FRONTEND_STATUS" = "YES" ]; then

        STATUS="FRONTEND_ONLY"

    elif [ "$GIT_STATUS" = "YES" ]; then

        STATUS="GIT_HISTORY_ONLY_OR_LEGACY"

    elif [ "$DEFAULT_STATUS" != "NO" ]; then

        STATUS="DECLARED_OR_DEFAULT_ONLY"

    fi

    printf \
        '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$VAR" \
        "$ENV_STATUS" \
        "$CONFIG_STATUS" \
        "$COMPOSE_STATUS" \
        "$RUNTIME_STATUS" \
        "$CONSUMER_STATUS" \
        "$FRONTEND_STATUS" \
        "$GIT_STATUS" \
        "$DEFAULT_STATUS" \
        "$CONFLICT_STATUS" \
        "$STATUS" \
        >> "$MATRIX"

done < "$MATRIX_VARS"

rm -f "$MATRIX_VARS"

###############################################################################
# 19. MATRIX SUMMARY
###############################################################################

section "19. CONFIGURATION MATRIX SUMMARY"

echo "Matrix file:"
echo "$MATRIX"

echo
echo "CONNECTED:"
awk -F'\t' \
    'NR > 1 && $11 == "CONNECTED" {print $1}' \
    "$MATRIX" |
tee -a "$RAW"

echo
echo "CONFLICTS:"
awk -F'\t' \
    'NR > 1 && $10 != "NO" {print $1 "\t" $10}' \
    "$MATRIX" |
tee -a "$RAW"

echo
echo "FRONTEND EXPOSED VARIABLES:"
awk -F'\t' \
    'NR > 1 && $7 == "YES" {print $1}' \
    "$MATRIX" |
tee -a "$RAW"

echo
echo "GIT-HISTORY VARIABLE NAMES:"
awk -F'\t' \
    'NR > 1 && $8 == "YES" {print $1}' \
    "$MATRIX" |
tee -a "$RAW"

echo
echo "STATUS COUNTS:"
awk -F'\t' '
    NR > 1 {
        count[$11]++
    }
    END {
        for (x in count)
            print x "\t" count[x]
    }
' "$MATRIX" |
sort |
tee -a "$RAW"

###############################################################################
# 20. COMPLETE
###############################################################################

section "20. CONFIGURATION AUTHORITY AUDIT COMPLETE"

echo "The audit distinguishes:"
echo
echo "  1. VARIABLE EXISTS"
echo "  2. VARIABLE REFERENCED"
echo "  3. VARIABLE CONSUMED BY RUNTIME"
echo "  4. VARIABLE HAS ENV SOURCE"
echo "  5. VARIABLE HAS CONFIG DECLARATION"
echo "  6. VARIABLE HAS COMPOSE SOURCE"
echo "  7. VARIABLE EXPOSED TO FRONTEND"
echo "  8. VARIABLE NAME EXISTS IN GIT HISTORY"
echo "  9. VARIABLE HAS DEFAULT/DECLARATION"
echo " 10. MULTIPLE AUTHORITIES / CONFLICTS"
echo
echo "Secret values remain redacted."
echo "Git history checks variable names, not secret values."
echo
echo "=========================================================================="
echo "AUDIT OUTPUT"
echo "=========================================================================="
echo
echo "Directory:"
echo "$OUT_DIR"
echo
echo "Raw:"
echo "$RAW"
echo
echo "Compose:"
echo "$COMPOSE"
echo
echo "Frontend:"
echo "$FRONT"
echo
echo "Conflicts:"
echo "$CONFLICT"
echo
echo "Secret-name history:"
echo "$SECRET"
echo
echo "Configuration Authority Matrix:"
echo "$MATRIX"
echo
echo "=========================================================================="

###############################################################################
# END
###############################################################################
