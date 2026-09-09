#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$HOME/waste-platform}"
ENV_FILE="${ENV_FILE:-$ROOT/.env.production}"

EXPECTED_REGISTRY="ghcr.io/mefoku52-cmyk"

cd "$ROOT"

echo "=== CMEP REGISTRY + COMPOSE AUTHORITY CHECK ==="
echo

echo "=== 1. SOURCE IDENTITY ==="

REMOTE="$(git remote get-url origin 2>/dev/null || true)"
HEAD="$(git rev-parse HEAD 2>/dev/null || true)"

echo "ORIGIN=$REMOTE"
echo "HEAD=$HEAD"

if [ "$REMOTE" != "https://github.com/mefoku52-cmyk/waste-platform.git" ]; then
    echo "[FAIL] Unexpected origin repository"
    exit 1
fi

if [ -z "$HEAD" ]; then
    echo "[FAIL] Cannot determine git HEAD"
    exit 1
fi

echo "[PASS] Repository identity confirmed"
echo

echo "=== 2. REGISTRY AUTHORITY ==="

echo "EXPECTED_REGISTRY_IMAGE_PREFIX=$EXPECTED_REGISTRY"

if [ ! -f "$ENV_FILE" ]; then
    echo "[FAIL] Missing $ENV_FILE"
    exit 1
fi

CURRENT_REGISTRY="$(grep '^REGISTRY_IMAGE_PREFIX=' "$ENV_FILE" | head -n1 | cut -d= -f2- || true)"

if [ "$CURRENT_REGISTRY" != "$EXPECTED_REGISTRY" ]; then
    echo "[FAIL] REGISTRY_IMAGE_PREFIX mismatch"
    echo "CURRENT=${CURRENT_REGISTRY:-<missing>}"
    echo "EXPECTED=$EXPECTED_REGISTRY"
    exit 1
fi

echo "REGISTRY_IMAGE_PREFIX=$CURRENT_REGISTRY"
echo "[PASS] Registry authority confirmed"
echo

echo "=== 3. RELEASE IDENTITY ==="

RELEASE_ID="sha-${HEAD}"
IMAGE_TAG="release-${HEAD}"

echo "RELEASE_ID=$RELEASE_ID"
echo "IMAGE_TAG=$IMAGE_TAG"

echo "[PASS] Release identity derived from current Git HEAD"
echo

echo "=== 4. COMPOSE CONFIGURATION ==="

CONFIG_FILE="$ROOT/.cmep-compose-config-check-${HEAD}.yml"
ERROR_FILE="$ROOT/.cmep-compose-config-error-${HEAD}.txt"

rm -f "$CONFIG_FILE" "$ERROR_FILE"

if REGISTRY_IMAGE_PREFIX="$EXPECTED_REGISTRY" \
   RELEASE_ID="$RELEASE_ID" \
   IMAGE_TAG="$IMAGE_TAG" \
   docker compose --env-file "$ENV_FILE" config \
   >"$CONFIG_FILE" 2>"$ERROR_FILE"; then

    echo "[PASS] docker compose config"

else

    echo "[FAIL] docker compose config"

    sed \
        -e 's/\(POSTGRES_PASSWORD:\).*/\1 <redacted>/' \
        -e 's/\(JWT_SECRET_KEY:\).*/\1 <redacted>/' \
        -e 's/\(JWT_REFRESH_SECRET_KEY:\).*/\1 <redacted>/' \
        "$ERROR_FILE" 2>/dev/null || true

    rm -f "$CONFIG_FILE" "$ERROR_FILE"
    exit 1
fi

echo

echo "=== 5. RESOLVED CMEP IMAGES ==="

grep -nE 'image:.*(cmep-api|cmep-web)' "$CONFIG_FILE" || true

echo

echo "=== 6. IMAGE IDENTITY CHECK ==="

if grep -q "ghcr.io/mefoku52-cmyk/cmep-api:${IMAGE_TAG}" "$CONFIG_FILE"; then
    echo "[PASS] cmep-api release image identity"
else
    echo "[FAIL] cmep-api release image identity mismatch"
    rm -f "$CONFIG_FILE" "$ERROR_FILE"
    exit 1
fi

if grep -q "ghcr.io/mefoku52-cmyk/cmep-web:${IMAGE_TAG}" "$CONFIG_FILE"; then
    echo "[PASS] cmep-web release image identity"
else
    echo "[FAIL] cmep-web release image identity mismatch"
    rm -f "$CONFIG_FILE" "$ERROR_FILE"
    exit 1
fi

echo

rm -f "$CONFIG_FILE" "$ERROR_FILE"

echo "=== RESULT ==="
echo "REGISTRY_AUTHORITY=CONFIRMED"
echo "REGISTRY_IMAGE_PREFIX=$EXPECTED_REGISTRY"
echo "RELEASE_ID=$RELEASE_ID"
echo "IMAGE_TAG=$IMAGE_TAG"
echo "COMPOSE_INTERPOLATION=PASS"
echo "IMAGE_IDENTITY=PASS"
echo "NO_DEPLOY_PERFORMED=1"
echo
