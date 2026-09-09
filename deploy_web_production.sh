#!/data/data/com.termux/files/usr/bin/bash
set -u

cd "$HOME/waste-platform" || exit 1

export DOCKER_HOST=tcp://127.0.0.1:32376

NEW_IMAGE="waste-platform-web:c1014eeb-browser-api-proxy-staticfix"
PROD="cmep-web"
NETWORK="waste-platform_cmep-network"
PORT="3101"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="${PROD}-rollback-${TS}"

OLD_IMAGE="$(docker inspect "$PROD" --format '{{.Config.Image}}' 2>/dev/null || true)"
OLD_STATE="$(docker inspect "$PROD" --format '{{.State.Status}}' 2>/dev/null || true)"

echo "============================================================"
echo "PRODUCTION WEB DEPLOY"
echo "============================================================"
echo "NEW_IMAGE=$NEW_IMAGE"
echo "PRODUCTION=$PROD"
echo "NETWORK=$NETWORK"
echo "OLD_IMAGE=$OLD_IMAGE"
echo "OLD_STATE=$OLD_STATE"
echo "============================================================"

fail() {
    echo
    echo "============================================================"
    echo "[FAIL] $1"
    echo "============================================================"
    exit 1
}

rollback() {
    echo
    echo "============================================================"
    echo "AUTOMATIC PRODUCTION ROLLBACK"
    echo "============================================================"

    docker rm -f "$PROD" >/dev/null 2>&1 || true

    if docker inspect "$BACKUP" >/dev/null 2>&1; then
        docker rename "$BACKUP" "$PROD" >/dev/null 2>&1 || true
        docker start "$PROD" >/dev/null 2>&1 || true
    fi

    sleep 5

    HTTP="$(curl -sS -o /dev/null -w '%{http_code}' \
        --connect-timeout 5 --max-time 10 \
        "http://127.0.0.1:${PORT}/" 2>/dev/null || echo 000)"

    echo "ROLLBACK_HTTP=$HTTP"

    if [ "$HTTP" = "200" ]; then
        echo "[PASS] PRODUCTION_ROLLBACK"
    else
        echo "[WARN] ROLLBACK_HTTP=$HTTP"
    fi

    exit 1
}

echo
echo "=== 1. DOCKER ==="
docker version >/dev/null 2>&1 || fail "DOCKER_UNAVAILABLE"
echo "[PASS] DOCKER"

echo
echo "=== 2. NEW IMAGE ==="
docker image inspect "$NEW_IMAGE" >/dev/null 2>&1 || fail "NEW_IMAGE_NOT_FOUND"
echo "[PASS] NEW_IMAGE_PRESENT"

echo
echo "=== 3. NETWORK ==="
docker network inspect "$NETWORK" >/dev/null 2>&1 || fail "NETWORK_NOT_FOUND"
echo "[PASS] NETWORK"

echo
echo "=== 4. API ==="
API_STATE="$(docker inspect cmep-api --format '{{.State.Status}}' 2>/dev/null || true)"
echo "API_STATE=$API_STATE"

[ "$API_STATE" = "running" ] || fail "CMEP_API_NOT_RUNNING"

echo "[PASS] CMEP_API_RUNNING"

echo
echo "=== 5. SAVE PRODUCTION CONTAINER ==="

if [ -z "$OLD_IMAGE" ]; then
    fail "PRODUCTION_CONTAINER_NOT_FOUND"
fi

echo "BACKUP=$BACKUP"

docker rename "$PROD" "$BACKUP" || fail "PRODUCTION_RENAME_FAILED"

echo "[PASS] PRODUCTION_BACKUP"

echo
echo "=== 6. START NEW PRODUCTION ==="

docker run -d \
    --name "$PROD" \
    --network "$NETWORK" \
    -p "${PORT}:3001" \
    "$NEW_IMAGE" >/dev/null 2>&1 || {
        docker rename "$BACKUP" "$PROD" >/dev/null 2>&1 || true
        docker start "$PROD" >/dev/null 2>&1 || true
        fail "NEW_PRODUCTION_START_FAILED"
    }

echo "[PASS] NEW_PRODUCTION_STARTED"

echo
echo "=== 7. WAIT FOR NEXT.JS ==="

READY=0

for i in $(seq 1 150); do
    STATE="$(docker inspect "$PROD" --format '{{.State.Status}}' 2>/dev/null || true)"

    if [ "$STATE" != "running" ]; then
        echo "PRODUCTION_STATE=$STATE"
        echo
        echo "=== PRODUCTION LOG ==="
        docker logs --tail 100 "$PROD" 2>&1 || true
        rollback
    fi

    HTTP="$(curl -sS -o /dev/null -w '%{http_code}' \
        --connect-timeout 2 --max-time 5 \
        "http://127.0.0.1:${PORT}/" 2>/dev/null || echo 000)"

    if [ "$HTTP" = "200" ]; then
        READY=1
        echo "NEXT_READY_AFTER=$((i * 2))s"
        break
    fi

    sleep 2
done

[ "$READY" = "1" ] || rollback

echo "[PASS] PRODUCTION_HTTP"

echo
echo "=== 8. API PROXY ==="

AUTH_HTTP="$(curl -sS -o /dev/null -w '%{http_code}' \
    --connect-timeout 5 --max-time 10 \
    "http://127.0.0.1:${PORT}/api/v1/auth/me" 2>/dev/null || echo 000)"

echo "AUTH_ME_HTTP=$AUTH_HTTP"

[ "$AUTH_HTTP" = "401" ] || rollback

echo "[PASS] API_PROXY"

echo
echo "=== 9. STATIC ASSET ==="

ASSET="$(docker exec "$PROD" sh -c \
    'find /app/.next/static/chunks -maxdepth 1 -type f -name "webpack-*.js" | head -n 1' \
    2>/dev/null || true)"

if [ -z "$ASSET" ]; then
    echo "STATIC_ASSET_NOT_FOUND"
    rollback
fi

ASSET_URL="/_next/static/chunks/$(basename "$ASSET")"

STATIC_HTTP="$(curl -sS -o /dev/null -w '%{http_code}' \
    --connect-timeout 5 --max-time 10 \
    "http://127.0.0.1:${PORT}${ASSET_URL}" 2>/dev/null || echo 000)"

echo "ASSET=$ASSET"
echo "ASSET_URL=$ASSET_URL"
echo "STATIC_HTTP=$STATIC_HTTP"

[ "$STATIC_HTTP" = "200" ] || rollback

echo "[PASS] STATIC_ASSET"

echo
echo "=== 10. PRODUCTION IMAGE ==="

RUNNING_IMAGE="$(docker inspect "$PROD" --format '{{.Config.Image}}')"
RUNNING_STATE="$(docker inspect "$PROD" --format '{{.State.Status}}')"

echo "RUNNING_IMAGE=$RUNNING_IMAGE"
echo "RUNNING_STATE=$RUNNING_STATE"

[ "$RUNNING_IMAGE" = "$NEW_IMAGE" ] || rollback
[ "$RUNNING_STATE" = "running" ] || rollback

echo "[PASS] NEW_IMAGE_RUNNING"

echo
echo "=== 11. API STILL RUNNING ==="

API_STATE="$(docker inspect cmep-api --format '{{.State.Status}}')"
echo "API_STATE=$API_STATE"

[ "$API_STATE" = "running" ] || rollback

echo "[PASS] API_UNTOUCHED"

echo
echo "=== 12. FINAL PRODUCTION STATUS ==="

docker ps \
    --filter "name=cmep-web" \
    --format 'NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}} PORTS={{.Ports}}'

echo
echo "============================================================"
echo "PRODUCTION WEB DEPLOYMENT COMPLETE"
echo "============================================================"
echo "IMAGE=$NEW_IMAGE"
echo "PRODUCTION=$PROD"
echo "HTTP=200"
echo "API_PROXY=401"
echo "STATIC_ASSET=200"
echo "API=$API_STATE"
echo "============================================================"
echo
echo "ROLLBACK_CONTAINER=$BACKUP"
echo "The rollback container is intentionally preserved."
echo "============================================================"
