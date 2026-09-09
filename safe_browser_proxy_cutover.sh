#!/usr/bin/env bash
set -u

export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:32376}"

IMAGE="waste-platform-web:c1014eeb-browser-api-proxy-staticfix"
PREVIEW="cmep-web-preview"
TEST="cmep-web-browser-proxy-test"
NETWORK="waste-platform_cmep-network"
PORT="3101"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="${PREVIEW}-rollback-${STAMP}"

CUTOVER_DONE=0

log() {
    echo
    echo "=== $1 ==="
}

fail() {
    echo
    echo "============================================================"
    echo "[FAIL] $1"
    echo "============================================================"

    if [ "$CUTOVER_DONE" = "1" ]; then
        echo
        echo "=== AUTOMATIC ROLLBACK ==="

        docker rm -f "$PREVIEW" >/dev/null 2>&1 || true

        if docker inspect "$BACKUP" >/dev/null 2>&1; then
            docker rename "$BACKUP" "$PREVIEW" >/dev/null 2>&1 || true
            docker start "$PREVIEW" >/dev/null 2>&1 || true

            for n in $(seq 1 60); do
                CODE="$(curl -sS -o /dev/null -w '%{http_code}' \
                    --max-time 2 \
                    "http://127.0.0.1:${PORT}/" \
                    2>/dev/null || true)"

                if [ "$CODE" = "200" ]; then
                    echo "[PASS] ROLLBACK_HTTP=200"
                    break
                fi

                sleep 1
            done
        else
            echo "[WARN] ROLLBACK_CONTAINER_NOT_FOUND"
        fi
    fi

    echo
    echo "=== PREVIEW ==="
    docker ps -a \
        --filter "name=^${PREVIEW}$" \
        --format 'NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}} PORTS={{.Ports}}' \
        2>/dev/null || true

    echo
    echo "=== PRODUCTION READ-ONLY ==="
    docker ps -a \
        --filter "name=^cmep-web$" \
        --format 'NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}}' \
        2>/dev/null || true

    exit 1
}

cleanup_test() {
    docker rm -f "$TEST" >/dev/null 2>&1 || true
}

trap cleanup_test EXIT

echo "============================================================"
echo "SAFE BROWSER-PROXY CUTOVER"
echo "============================================================"
echo "IMAGE=$IMAGE"
echo "PREVIEW=$PREVIEW"
echo "PORT=$PORT"
echo "NETWORK=$NETWORK"
echo "PRODUCTION=UNTOUCHED"
echo "============================================================"

log "1. DOCKER"

docker version >/dev/null 2>&1 || fail "DOCKER_UNAVAILABLE"

echo "[PASS] DOCKER"

log "2. IMAGE"

docker image inspect "$IMAGE" >/dev/null 2>&1 \
    || fail "NEW_IMAGE_NOT_FOUND"

echo "[PASS] IMAGE_PRESENT"

log "3. NETWORK"

docker network inspect "$NETWORK" >/dev/null 2>&1 \
    || fail "NETWORK_NOT_FOUND"

echo "[PASS] NETWORK"

log "4. API CONTAINER"

API_STATE="$(docker inspect -f '{{.State.Status}}' cmep-api 2>/dev/null || true)"

echo "API_STATE=${API_STATE:-missing}"

[ "$API_STATE" = "running" ] \
    || fail "CMEP_API_NOT_RUNNING"

echo "[PASS] C MEP_API_RUNNING"

log "5. PRODUCTION SNAPSHOT"

PROD_IMAGE="$(docker inspect -f '{{.Config.Image}}' cmep-web 2>/dev/null || true)"
PROD_STATE="$(docker inspect -f '{{.State.Status}}' cmep-web 2>/dev/null || true)"

echo "PRODUCTION_IMAGE=${PROD_IMAGE:-missing}"
echo "PRODUCTION_STATE=${PROD_STATE:-missing}"

log "6. CURRENT PREVIEW"

OLD_IMAGE="$(docker inspect -f '{{.Config.Image}}' "$PREVIEW" 2>/dev/null || true)"
OLD_STATE="$(docker inspect -f '{{.State.Status}}' "$PREVIEW" 2>/dev/null || true)"

if [ -z "$OLD_IMAGE" ]; then
    fail "CURRENT_PREVIEW_NOT_FOUND"
fi

echo "OLD_IMAGE=$OLD_IMAGE"
echo "OLD_STATE=$OLD_STATE"

[ "$OLD_STATE" = "running" ] \
    || fail "CURRENT_PREVIEW_NOT_RUNNING"

echo "[PASS] CURRENT_PREVIEW"

log "7. CLEAN ISOLATED TEST"

cleanup_test

CID="$(
    docker run -d \
        --name "$TEST" \
        --network "$NETWORK" \
        "$IMAGE" \
        2>/dev/null || true
)"

[ -n "$CID" ] \
    || fail "ISOLATED_TEST_START_FAILED"

echo "[PASS] ISOLATED_TEST_STARTED"

log "8. WAIT FOR NEW NEXT.JS"

READY=0

for i in $(seq 1 120); do

    STATE="$(docker inspect -f '{{.State.Status}}' "$TEST" \
        2>/dev/null || echo missing)"

    if [ "$STATE" != "running" ]; then
        docker logs --tail 100 "$TEST" 2>&1 || true
        fail "ISOLATED_TEST_CONTAINER_STOPPED"
    fi

    CODE="$(
        docker exec "$TEST" node -e '
const http=require("http");
const r=http.get("http://127.0.0.1:3001/",{timeout:2000},res=>{
  console.log(res.statusCode);
  res.resume();
});
r.on("timeout",()=>{r.destroy();process.exit(2)});
r.on("error",()=>process.exit(2));
' 2>/dev/null || true
    )"

    if echo "$CODE" | grep -qx "200"; then
        READY=1
        echo "[PASS] NEXT_READY_AFTER=${i}s"
        break
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "waited=${i}s"
    fi

    sleep 1
done

[ "$READY" = "1" ] \
    || {
        docker logs --tail 100 "$TEST" 2>&1 || true
        fail "NEXT_NOT_READY"
    }

log "9. ISOLATED API PROXY"

PROXY_CODE="$(
    docker exec "$TEST" node -e '
const http=require("http");
const r=http.get("http://127.0.0.1:3001/api/v1/auth/me",{timeout:10000},res=>{
  console.log(res.statusCode);
  res.resume();
});
r.on("timeout",()=>{r.destroy();process.exit(2)});
r.on("error",()=>process.exit(2));
' 2>/dev/null || true
)"

echo "AUTH_ME_HTTP=${PROXY_CODE:-000}"

echo "$PROXY_CODE" | grep -qx "401" \
    || fail "API_PROXY_EXPECTED_401_GOT_${PROXY_CODE:-EMPTY}"

echo "[PASS] API_PROXY"

log "10. ISOLATED STATIC ASSET"

ASSET="$(
    docker exec "$TEST" sh -c \
        'find /app/.next/static -type f -name "webpack-*.js" | head -1' \
        2>/dev/null || true
)"

echo "ASSET=${ASSET:-missing}"

[ -n "$ASSET" ] \
    || fail "WEBPACK_ASSET_MISSING"

ASSET_URL="/_next/static/${ASSET#/app/.next/static/}"

echo "ASSET_URL=$ASSET_URL"

STATIC_CODE="$(
    docker exec "$TEST" node -e '
const http=require("http");
const u=process.argv[1];
const r=http.get("http://127.0.0.1:3001"+u,{timeout:10000},res=>{
  console.log(res.statusCode);
  res.resume();
});
r.on("timeout",()=>{r.destroy();process.exit(2)});
r.on("error",()=>process.exit(2));
' "$ASSET_URL" 2>/dev/null || true
)"

echo "STATIC_HTTP=${STATIC_CODE:-000}"

echo "$STATIC_CODE" | grep -qx "200" \
    || fail "STATIC_ASSET_EXPECTED_200_GOT_${STATIC_CODE:-EMPTY}"

echo "[PASS] STATIC_ASSET"

log "11. ISOLATED DIRECT API"

DIRECT_CODE="$(
    docker exec "$TEST" node -e '
const http=require("http");
const r=http.get("http://cmep-api:8000/health",{timeout:10000},res=>{
  console.log(res.statusCode);
  res.resume();
});
r.on("timeout",()=>{r.destroy();process.exit(2)});
r.on("error",()=>process.exit(2));
' 2>/dev/null || true
)"

echo "DIRECT_API_HTTP=${DIRECT_CODE:-000}"

echo "$DIRECT_CODE" | grep -qx "200" \
    || fail "DIRECT_API_EXPECTED_200_GOT_${DIRECT_CODE:-EMPTY}"

echo "[PASS] DIRECT_API"

log "12. ISOLATED TEST CLEANUP"

cleanup_test

if docker inspect "$TEST" >/dev/null 2>&1; then
    fail "TEST_CLEANUP_FAILED"
fi

echo "[PASS] TEST_CLEANUP"

echo
echo "============================================================"
echo "NEW IMAGE FULLY VALIDATED"
echo "============================================================"
echo "API proxy:     401 PASS"
echo "Static asset:  200 PASS"
echo "Direct API:    200 PASS"
echo "============================================================"

log "13. BACKUP CURRENT PREVIEW"

if docker inspect "$BACKUP" >/dev/null 2>&1; then
    docker rm -f "$BACKUP" >/dev/null 2>&1 || true
fi

docker rename "$PREVIEW" "$BACKUP" \
    || fail "PREVIEW_BACKUP_FAILED"

echo "BACKUP=$BACKUP"
echo "[PASS] PREVIEW_BACKUP"

log "14. START NEW PREVIEW"

NEW_CID="$(
    docker run -d \
        --name "$PREVIEW" \
        --network "$NETWORK" \
        -p "127.0.0.1:${PORT}:3001" \
        "$IMAGE" \
        2>/dev/null || true
)"

if [ -z "$NEW_CID" ]; then
    CUTOVER_DONE=1
    fail "NEW_PREVIEW_START_FAILED"
fi

CUTOVER_DONE=1

echo "[PASS] NEW_PREVIEW_STARTED"

log "15. WAIT FOR HOST PREVIEW"

READY=0

for i in $(seq 1 120); do

    STATE="$(docker inspect -f '{{.State.Status}}' "$PREVIEW" \
        2>/dev/null || echo missing)"

    if [ "$STATE" != "running" ]; then
        docker logs --tail 100 "$PREVIEW" 2>&1 || true
        fail "NEW_PREVIEW_STOPPED"
    fi

    CODE="$(
        curl -sS \
            -o /dev/null \
            -w '%{http_code}' \
            --max-time 3 \
            "http://127.0.0.1:${PORT}/" \
            2>/dev/null || true
    )"

    if [ "$CODE" = "200" ]; then
        READY=1
        echo "[PASS] HOST_PREVIEW_READY_AFTER=${i}s"
        break
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "waited=${i}s http=${CODE:-000}"
    fi

    sleep 1
done

[ "$READY" = "1" ] || fail "HOST_PREVIEW_NOT_READY"

log "16. HOST API PROXY"

HOST_AUTH="$(
    curl -sS \
        -o /dev/null \
        -w '%{http_code}' \
        --max-time 10 \
        "http://127.0.0.1:${PORT}/api/v1/auth/me" \
        2>/dev/null || true
)"

echo "HOST_AUTH_ME_HTTP=${HOST_AUTH:-000}"

[ "$HOST_AUTH" = "401" ] \
    || fail "HOST_API_PROXY_EXPECTED_401_GOT_${HOST_AUTH:-EMPTY}"

echo "[PASS] HOST_API_PROXY"

log "17. HOST STATIC ASSET"

HOST_STATIC="$(
    curl -sS \
        -o /dev/null \
        -w '%{http_code}' \
        --max-time 10 \
        "http://127.0.0.1:${PORT}${ASSET_URL}" \
        2>/dev/null || true
)"

echo "HOST_STATIC_HTTP=${HOST_STATIC:-000}"

[ "$HOST_STATIC" = "200" ] \
    || fail "HOST_STATIC_EXPECTED_200_GOT_${HOST_STATIC:-EMPTY}"

echo "[PASS] HOST_STATIC_ASSET"

log "18. PRODUCTION IMMUTABILITY"

PROD_IMAGE_AFTER="$(docker inspect -f '{{.Config.Image}}' cmep-web 2>/dev/null || true)"
PROD_STATE_AFTER="$(docker inspect -f '{{.State.Status}}' cmep-web 2>/dev/null || true)"

echo "BEFORE_IMAGE=${PROD_IMAGE:-missing}"
echo "AFTER_IMAGE=${PROD_IMAGE_AFTER:-missing}"
echo "BEFORE_STATE=${PROD_STATE:-missing}"
echo "AFTER_STATE=${PROD_STATE_AFTER:-missing}"

[ "$PROD_IMAGE_AFTER" = "$PROD_IMAGE" ] \
    || fail "PRODUCTION_IMAGE_CHANGED"

[ "$PROD_STATE_AFTER" = "$PROD_STATE" ] \
    || fail "PRODUCTION_STATE_CHANGED"

echo "[PASS] PRODUCTION_UNTOUCHED"

echo
echo "============================================================"
echo "PREVIEW CUTOVER SUCCESS"
echo "============================================================"

docker ps \
    --filter "name=^${PREVIEW}$" \
    --format 'NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}} PORTS={{.Ports}}'

echo
echo "ROLLBACK_CONTAINER=$BACKUP"

docker ps -a \
    --filter "name=^${BACKUP}$" \
    --format 'NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}} PORTS={{.Ports}}'

echo
echo "PRODUCTION: UNCHANGED"

echo
echo "============================================================"
echo "FINAL RESULT: PASS"
echo "============================================================"
echo "NEW IMAGE       = VALIDATED"
echo "NEXT.JS         = PASS"
echo "API PROXY       = 401 PASS"
echo "STATIC ASSET    = 200 PASS"
echo "DIRECT API      = 200 PASS"
echo "PREVIEW :3101   = PASS"
echo "PRODUCTION      = UNTOUCHED"
echo "ROLLBACK        = $BACKUP"
echo "============================================================"
