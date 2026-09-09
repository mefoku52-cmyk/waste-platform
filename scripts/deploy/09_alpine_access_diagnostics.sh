#!/usr/bin/env bash
set -u

VM_DIR="$HOME/alpine-vm/qemu-docker"

echo "=== CMEP ALPINE ACCESS DIAGNOSTICS ==="
echo

echo "=== 1. QEMU STATE ==="

QEMU_PID="$(pgrep -f 'qemu-system-x86_64.*alpine\.qcow2' | head -n1 || true)"

if [ -n "$QEMU_PID" ]; then
    echo "[RUNNING] QEMU PID=$QEMU_PID"
    tr '\0' ' ' < "/proc/$QEMU_PID/cmdline" 2>/dev/null || true
    echo
else
    echo "[STOPPED] No Alpine QEMU process"
fi

echo

echo "=== 2. SSH PORTS ==="

if command -v ss >/dev/null 2>&1; then
    ss -lnt 2>/dev/null | grep -E ':(32222|32375|32376)[[:space:]]' || \
        echo "[NONE] 32222/32375/32376"
fi

echo

echo "=== 3. SSH CLIENT ==="

if command -v ssh >/dev/null 2>&1; then
    echo "ssh=$(command -v ssh)"
else
    echo "[MISSING] ssh client"
fi

echo

echo "=== 4. VM DISK ==="

if [ -f "$VM_DIR/alpine.qcow2" ]; then
    ls -lh "$VM_DIR/alpine.qcow2"
else
    echo "[MISSING] alpine.qcow2"
fi

echo

echo "=== 5. INSTALL FLAG ==="

if [ -f "$VM_DIR/alpine-installed.flag" ]; then
    echo "[PRESENT] alpine-installed.flag"
else
    echo "[MISSING] alpine-installed.flag"
fi

echo

echo "=== 6. DOCUMENTATION INDICATORS ==="

if grep -RInE \
    'apk add docker|rc-update add docker|service docker start|dockerd|hostfwd' \
    "$VM_DIR" \
    2>/dev/null | head -n 100
then
    true
else
    echo "[NONE] Docker installation/start references"
fi

echo

echo "=== 7. QEMU PROCESS AGE / OWNER ==="

if [ -n "$QEMU_PID" ]; then
    ps -o pid,ppid,lstart,etime,args -p "$QEMU_PID" 2>/dev/null || true
fi

echo

echo "=== 8. EXISTING REPAIR SCRIPT SAFETY CHECK ==="

if [ -f "$HOME/alpine-vm/repair_and_boot_alpine.sh" ]; then
    echo "[FOUND] repair_and_boot_alpine.sh"
    grep -nE \
        'rm -f alpine-installed.flag|rm -f|mkfs|qemu-img|boot-install|setup-alpine' \
        "$HOME/alpine-vm/repair_and_boot_alpine.sh" \
        2>/dev/null || true
fi

echo

echo "=== RESULT ==="
echo "ALPINE_ACCESS_DIAGNOSTICS=COMPLETE"
echo "NO_VM_STARTED=0"
echo "NO_VM_STOPPED=0"
echo "NO_FILES_MODIFIED=1"
echo "NO_DEPLOY_PERFORMED=1"
echo
