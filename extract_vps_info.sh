#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="$HOME/waste-platform/VPS_LOCAL_DISCOVERY_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "LOCAL VPS / SERVER INFORMATION DISCOVERY"
echo "READ ONLY"
echo "NO SSH CONNECTION"
echo "NO DEPLOY"
echo "NO MODIFICATION"
echo "============================================================"
echo

echo "===== SYSTEM ====="
printf 'DATE='; date -Is
printf 'USER='; id -un
printf 'HOME=%s\n' "$HOME"
printf 'PWD='; pwd
printf 'HOSTNAME='; hostname
echo

echo "===== WASTE-PLATFORM ====="
if [ -d "$HOME/waste-platform" ]; then
    echo "PROJECT=FOUND"
    printf 'PROJECT_ROOT='
    cd "$HOME/waste-platform" && pwd
    echo
    echo "--- project git ---"
    if [ -d "$HOME/waste-platform/.git" ]; then
        echo "GIT=FOUND"
        git -C "$HOME/waste-platform" remote -v 2>/dev/null || true
        git -C "$HOME/waste-platform" branch --show-current 2>/dev/null || true
        git -C "$HOME/waste-platform" rev-parse --short HEAD 2>/dev/null || true
    else
        echo "GIT=NOT_FOUND"
    fi
else
    echo "PROJECT=NOT_FOUND"
fi
echo

echo "===== ENVIRONMENT VARIABLES: SERVER / DEPLOY / REGISTRY ====="
env | grep -Ei \
'CONTABO|VPS|SERVER|HOST|SSH|DEPLOY|REGISTRY|IMAGE_TAG|RELEASE_ID|DOMAIN|DOMAIN_NAME|PUBLIC_IP|SERVER_IP' \
| sed -E 's/(PASSWORD|PASSWD|TOKEN|SECRET|PRIVATE_KEY|API_KEY|ACCESS_KEY)=.*/\1=[REDACTED]/I' \
|| true
echo

echo "===== SHELL HISTORY: SERVER / SSH / DEPLOY REFERENCES ====="
for f in \
    "$HOME/.bash_history" \
    "$HOME/.zsh_history" \
    "$HOME/.history"
do
    if [ -f "$f" ]; then
        echo "--- $f ---"
        grep -Ein \
        'ssh |scp |sftp |rsync |contabo|vps|server|deploy|docker compose|docker-compose|registry|image_tag|release_id|production' \
        "$f" 2>/dev/null \
        | tail -300 \
        | sed -E \
          's/(sshpass[^ ]*[[:space:]]+)?-p[[:space:]]+[^[:space:]]+/-p [REDACTED]/g;
           s/(password|passwd|token|secret|api[_-]?key)[=:][^[:space:]]+/\1=[REDACTED]/Ig' \
        || true
    fi
done
echo

echo "===== SSH CONFIG ====="
if [ -d "$HOME/.ssh" ]; then
    echo "SSH_DIR=FOUND"
    find "$HOME/.ssh" -maxdepth 2 -type f -print 2>/dev/null \
    | sed -E 's#(.*/)?([^/]+)$#\2#' \
    | sort -u

    if [ -f "$HOME/.ssh/config" ]; then
        echo
        echo "--- ~/.ssh/config SAFE FIELDS ---"
        grep -Ein \
        '^[[:space:]]*(Host|HostName|Port|User|IdentityFile)[[:space:]]+' \
        "$HOME/.ssh/config" 2>/dev/null \
        || true
    fi
else
    echo "SSH_DIR=NOT_FOUND"
fi
echo

echo "===== KNOWN SSH HOSTS ====="
if [ -f "$HOME/.ssh/known_hosts" ]; then
    echo "KNOWN_HOSTS=FOUND"
    wc -l "$HOME/.ssh/known_hosts"
    echo "--- host fingerprints / names only ---"
    cut -d' ' -f1 "$HOME/.ssh/known_hosts" 2>/dev/null \
    | sort -u \
    | head -200
else
    echo "KNOWN_HOSTS=NOT_FOUND"
fi
echo

echo "===== PROJECT SERVER REFERENCES ====="
cd "$HOME/waste-platform" 2>/dev/null || true

grep -RInE \
--exclude-dir=.git \
--exclude-dir=node_modules \
--exclude-dir=.venv \
--exclude='*.log' \
--exclude='*.db' \
--exclude='*.sqlite' \
--exclude='known_hosts' \
'(ssh[[:space:]]+|scp[[:space:]]+|rsync[[:space:]]+|HostName|SERVER_HOST|SERVER_IP|VPS_HOST|VPS_IP|CONTABO|registry|docker login|docker push|docker pull|production)' \
. 2>/dev/null \
| head -1000 \
| sed -E \
's/(password|passwd|token|secret|api[_-]?key)[=:][^[:space:]]+/\1=[REDACTED]/Ig;
 s/(-----BEGIN [^-]+-----).*/\1 [REDACTED]/g' \
|| true
echo

echo "===== PRODUCTION RELEASE FILES ====="
find "$HOME/waste-platform" \
-maxdepth 5 \
-type f \
\( \
-name '*.env' \
-o -name '.env*' \
-o -name '*deploy*' \
-o -name '*production*' \
-o -name '*registry*' \
-o -name '*release*' \
-o -name '*server*' \
-o -name '*vps*' \
-o -name '*contabo*' \
\) \
-print 2>/dev/null \
| sort \
| head -1000
echo

echo "===== GIT REMOTES ====="
if [ -d "$HOME/waste-platform/.git" ]; then
    git -C "$HOME/waste-platform" remote -v 2>/dev/null || true
fi
echo

echo "===== NETWORK STATE: LOCAL ONLY ====="
printf 'DEFAULT_ROUTE='
ip route 2>/dev/null | grep '^default' | head -1 || true

printf 'LOCAL_ADDRESSES=\n'
ip -o addr 2>/dev/null | head -50 || true
echo

echo "===== DOCKER LOCAL STATE ====="
if command -v docker >/dev/null 2>&1; then
    docker --version 2>/dev/null || true
    docker compose version 2>/dev/null || true
else
    echo "DOCKER=NOT_INSTALLED"
fi
echo

echo "============================================================"
echo "DISCOVERY COMPLETE"
echo "OUTPUT=$OUT"
echo "============================================================"

} | tee "$OUT"

echo
echo "Súbor uložený:"
echo "$OUT"
