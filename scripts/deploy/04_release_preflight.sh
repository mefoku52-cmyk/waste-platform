#!/usr/bin/env bash
set -u

PROJECT_DIR="${PROJECT_DIR:-/data/data/com.termux/files/home/waste-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

cd "$PROJECT_DIR" || exit 1

echo "=== CMEP RELEASE PREFLIGHT ==="
echo

echo "=== 1. DEPLOY SCRIPT ==="
if bash -n scripts/deploy.sh; then
    echo "[PASS] scripts/deploy.sh syntax"
else
    echo "[FAIL] scripts/deploy.sh syntax"
fi

echo
echo "=== 2. PRODUCTION ENV PRESENCE ==="

for key in \
    POSTGRES_USER \
    POSTGRES_PASSWORD \
    POSTGRES_DB \
    DATABASE_URL \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    REGISTRY_IMAGE_PREFIX
do
    if grep -qE "^${key}=" "$ENV_FILE" 2>/dev/null; then
        value="$(grep -E "^${key}=" "$ENV_FILE" | head -n1 | cut -d= -f2-)"
        if [ -n "$value" ]; then
            if [ "$key" = "REGISTRY_IMAGE_PREFIX" ]; then
                echo "[DEFINED] $key=$value"
            else
                echo "[DEFINED] $key=<redacted>"
            fi
        else
            echo "[EMPTY]   $key"
        fi
    else
        echo "[MISSING] $key"
    fi
done

echo
echo "=== 3. RELEASE STATE ==="

STATE_DIR="$PROJECT_DIR/.production-release/state"

for file in current-release.env previous-release.env; do
    path="$STATE_DIR/$file"

    if [ -f "$path" ]; then
        echo "--- $file ---"
        grep -E '^(RELEASE_ID|IMAGE_TAG)=' "$path" 2>/dev/null || true
    else
        echo "[MISSING] $file"
    fi
done

echo
echo "=== 4. GIT SOURCE IDENTITY ==="

GIT_SHA="$(git rev-parse HEAD 2>/dev/null || true)"

if [ -n "$GIT_SHA" ]; then
    echo "HEAD=$GIT_SHA"
    echo "RELEASE_ID_EXPECTED=sha-${GIT_SHA}"
    echo "IMAGE_TAG_EXPECTED=release-${GIT_SHA}"
else
    echo "[FAIL] Cannot determine git HEAD"
fi

echo
echo "=== 5. DOCKER CLIENT ==="

if command -v docker >/dev/null 2>&1; then
    docker --version
else
    echo "[FAIL] docker command missing"
fi

echo
echo "=== 6. DOCKER COMPOSE ==="

if docker compose version >/dev/null 2>&1; then
    docker compose version
else
    echo "[FAIL] docker compose unavailable"
fi

echo
echo "=== 7. DOCKER DAEMON ==="

if docker info >/dev/null 2>&1; then
    echo "[PASS] Docker daemon reachable"
else
    echo "[FAIL] Docker daemon NOT reachable"
    docker info 2>&1 | tail -n 5 || true
fi

echo
echo "=== 8. COMPOSE CONFIG WITH PRODUCTION ENV ==="

if [ ! -f "$ENV_FILE" ]; then
    echo "[FAIL] Missing $ENV_FILE"
elif [ ! -f "$COMPOSE_FILE" ]; then
    echo "[FAIL] Missing $COMPOSE_FILE"
else
    TMP="$PROJECT_DIR/reports/.compose-preflight.tmp"
    mkdir -p "$PROJECT_DIR/reports"

    if docker compose \
        --env-file "$ENV_FILE" \
        -f "$COMPOSE_FILE" \
        config >"$TMP" 2>&1
    then
        echo "[PASS] docker compose config"
    else
        echo "[FAIL] docker compose config"
        tail -n 20 "$TMP"
    fi

    rm -f "$TMP"
fi

echo
echo "=== 9. COMPOSE IMAGE DEFINITIONS ==="

grep -nE '^[[:space:]]+image:' "$COMPOSE_FILE" 2>/dev/null || true

echo
echo "=== 10. FINAL ==="

REGISTRY_OK=0
if grep -qE '^REGISTRY_IMAGE_PREFIX=.+$' "$ENV_FILE" 2>/dev/null; then
    REGISTRY_OK=1
fi

DOCKER_OK=0
if docker info >/dev/null 2>&1; then
    DOCKER_OK=1
fi

if [ "$REGISTRY_OK" -eq 1 ] && [ "$DOCKER_OK" -eq 1 ]; then
    echo "RELEASE_PREFLIGHT=PASS"
else
    echo "RELEASE_PREFLIGHT=BLOCKED"
    [ "$REGISTRY_OK" -eq 0 ] && echo "BLOCKER=REGISTRY_IMAGE_PREFIX"
    [ "$DOCKER_OK" -eq 0 ] && echo "BLOCKER=DOCKER_DAEMON"
fi
