#!/usr/bin/env bash
set -u

VM_DIR="$HOME/alpine-vm/qemu-docker"
HOST_PORT="32376"

echo "=== CMEP QEMU DOCKER API DIAGNOSTICS ==="
echo

echo "=== 1. RUNNING QEMU ==="
QEMU_PID="$(pgrep -f 'qemu-system-x86_64.*alpine\.qcow2' | head -n1 || true)"

if [ -n "$QEMU_PID" ]; then
    echo "[PASS] QEMU PID=$QEMU_PID"
    ps -fp "$QEMU_PID" 2>/dev/null || true
else
    echo "[FAIL] Alpine QEMU process not found"
fi
echo

echo "=== 2. QEMU COMMAND LINE ==="
if [ -n "$QEMU_PID" ]; then
    tr '\0' ' ' < "/proc/$QEMU_PID/cmdline" 2>/dev/null || true
    echo
fi
echo

echo "=== 3. HOST API PORT 32376 ==="

if command -v ss >/dev/null 2>&1; then
    ss -lnt 2>/dev/null | grep -E '(^|:)32376[[:space:]]' || \
        echo "[MISSING] TCP listener on 127.0.0.1:32376"
fi

if command -v nc >/dev/null 2>&1; then
    if nc -z -w 2 127.0.0.1 "$HOST_PORT" 2>/dev/null; then
        echo "[PASS] 127.0.0.1:$HOST_PORT accepts TCP"
    else
        echo "[FAIL] 127.0.0.1:$HOST_PORT does not accept TCP"
    fi
else
    echo "[INFO] nc not installed"
fi
echo

echo "=== 4. DOCKER TCP API PROBE ==="

if command -v curl >/dev/null 2>&1; then
    HTTP_CODE="$(
        curl \
            --silent \
            --show-error \
            --connect-timeout 2 \
            --max-time 5 \
            -o /dev/null \
            -w '%{http_code}' \
            "http://127.0.0.1:${HOST_PORT}/_ping" \
            2>/tmp/cmep_docker_api_probe_error.$$ \
        || true
    )"

    echo "HTTP_CODE=${HTTP_CODE:-<none>}"

    if [ "$HTTP_CODE" = "200" ]; then
        echo "[PASS] Docker API /_ping reachable"
    else
        echo "[FAIL] Docker API /_ping not reachable"
        if [ -s /tmp/cmep_docker_api_probe_error.$$ ]; then
            cat /tmp/cmep_docker_api_probe_error.$$
        fi
    fi

    rm -f /tmp/cmep_docker_api_probe_error.$$
else
    echo "[INFO] curl not installed"
fi
echo

echo "=== 5. EXISTING VM FILES ==="
if [ -d "$VM_DIR" ]; then
    find "$VM_DIR" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | sort
else
    echo "[FAIL] VM directory missing: $VM_DIR"
fi
echo

echo "=== 6. VM DOCUMENTATION ==="

for f in \
    "$VM_DIR/README-CMEP-DOCKER.txt" \
    "$VM_DIR/vm-setup-steps.txt"
do
    if [ -f "$f" ]; then
        echo
        echo "--- $f ---"
        cat "$f"
    fi
done

echo

echo "=== 7. BOOT SCRIPTS ==="

for f in \
    "$VM_DIR/boot-docker.sh" \
    "$VM_DIR/boot-docker-api.sh" \
    "$HOME/alpine-vm/repair_and_boot_alpine.sh"
do
    if [ -f "$f" ]; then
        echo
        echo "--- $f ---"
        sed -n '1,240p' "$f"
    fi
done

echo

echo "=== 8. DOCKER CLIENT TCP TEST ==="

DOCKER_HOST="tcp://127.0.0.1:${HOST_PORT}" docker version 2>&1 || true

echo

echo "=== RESULT ==="
echo "DOCKER_VM_API_DIAGNOSTICS=COMPLETE"
echo "NO_VM_STARTED=1"
echo "NO_FILES_MODIFIED=1"
echo "NO_DEPLOY_PERFORMED=1"
echo
