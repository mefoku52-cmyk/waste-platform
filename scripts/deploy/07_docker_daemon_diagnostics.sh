#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$HOME/waste-platform}"
SOCKET="${DOCKER_HOST:-unix:///data/data/com.termux/files/usr/var/run/docker.sock}"

echo "=== CMEP DOCKER DAEMON DIAGNOSTICS ==="
echo

echo "=== 1. DOCKER CLIENT ==="
docker version 2>&1 || true
echo

echo "=== 2. DOCKER INFO ==="
docker info 2>&1 || true
echo

echo "=== 3. DOCKER HOST ==="
echo "DOCKER_HOST=${DOCKER_HOST:-<unset>}"
echo "EXPECTED_SOCKET=$SOCKET"
echo

echo "=== 4. LOCAL DOCKER SOCKET ==="
SOCK_PATH="/data/data/com.termux/files/usr/var/run/docker.sock"

if [ -S "$SOCK_PATH" ]; then
    echo "[FOUND] $SOCK_PATH"
    ls -l "$SOCK_PATH" 2>/dev/null || true
else
    echo "[MISSING] $SOCK_PATH"
fi
echo

echo "=== 5. DOCKER PROCESSES ==="
ps -ef 2>/dev/null | grep -E '[d]ockerd|[d]ocker-proxy|[c]ontainerd' || true
echo

echo "=== 6. QEMU PROCESSES ==="
ps -ef 2>/dev/null | grep -E '[q]emu-system|[q]emu-kvm' || true
echo

echo "=== 7. ALPINE VM DIRECTORY ==="
for d in \
    "$HOME/alpine-vm" \
    "$HOME/alpine-vm/qemu-docker"
do
    if [ -d "$d" ]; then
        echo "[FOUND] $d"
        find "$d" -maxdepth 2 -type f -printf '%p\n' 2>/dev/null | sort | head -n 100
    else
        echo "[MISSING] $d"
    fi
done
echo

echo "=== 8. DOCKER START SCRIPTS ==="
for f in \
    "$HOME/alpine-vm/START_CMEP_DOCKER.sh" \
    "$HOME/alpine-vm/qemu-docker/START_CMEP_DOCKER.sh" \
    "$HOME/alpine-vm/boot-docker.sh" \
    "$HOME/alpine-vm/qemu-docker/boot-docker.sh" \
    "$HOME/alpine-vm/boot-docker-api.sh" \
    "$HOME/alpine-vm/qemu-docker/boot-docker-api.sh"
do
    if [ -f "$f" ]; then
        echo "[FOUND] $f"
        sed -n '1,220p' "$f" 2>/dev/null
        echo
    fi
done

echo "=== 9. LISTENING SOCKETS ==="
if command -v ss >/dev/null 2>&1; then
    ss -lntup 2>/dev/null || true
else
    echo "[INFO] ss not available"
fi
echo

echo "=== 10. UNIX SOCKET SEARCH ==="
find "$HOME" \
    /data/data/com.termux/files/usr/var/run \
    -maxdepth 5 \
    -type s \
    -name '*docker*' \
    -print 2>/dev/null | head -n 100 || true
echo

echo "=== 11. QEMU DIRECTORY METADATA ==="
if [ -d "$HOME/alpine-vm/qemu-docker" ]; then
    ls -lah "$HOME/alpine-vm/qemu-docker" 2>/dev/null || true
fi
echo

echo "=== RESULT ==="
echo "DOCKER_DAEMON_DIAGNOSTICS=COMPLETE"
echo "NO_FILES_MODIFIED=1"
echo "NO_DAEMON_STARTED=1"
echo "NO_DEPLOY_PERFORMED=1"
echo
