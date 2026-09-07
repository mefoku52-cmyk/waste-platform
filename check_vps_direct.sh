#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "============================================================"
echo "DIRECT VPS / PRODUCTION PRECHECK"
echo "NO DEPLOY"
echo "NO PROJECT MODIFICATION"
echo "NO R66"
echo "============================================================"
echo

read -rp "VPS SSH user (napr. root): " VPS_USER
read -rp "VPS host/IP: " VPS_HOST
read -rp "SSH port [22]: " VPS_PORT
VPS_PORT="${VPS_PORT:-22}"

echo
echo "============================================================"
echo "1. SSH CONNECTIVITY"
echo "============================================================"

if ssh \
    -o ConnectTimeout=10 \
    -o BatchMode=no \
    -p "$VPS_PORT" \
    "${VPS_USER}@${VPS_HOST}" \
    'printf "SSH_OK\n"; hostname; printf "DATE="; date -Is; printf "USER="; id -un; printf "PWD="; pwd'
then
    echo
    echo "SSH_STATUS=PASS"
else
    echo
    echo "SSH_STATUS=FAIL"
    exit 2
fi

echo
echo "============================================================"
echo "2. VPS DOCKER"
echo "============================================================"

ssh \
    -p "$VPS_PORT" \
    "${VPS_USER}@${VPS_HOST}" \
    '
set -u

printf "DOCKER_BINARY="
command -v docker || true

printf "DOCKER_VERSION="
docker --version 2>/dev/null || true

printf "COMPOSE_VERSION="
docker compose version 2>/dev/null || true

printf "DOCKER_DAEMON="
if docker info >/dev/null 2>&1; then
    echo "AVAILABLE"
else
    echo "UNAVAILABLE"
fi
'

echo
echo "============================================================"
echo "3. FIND WASTE-PLATFORM ON VPS"
echo "============================================================"

ssh \
    -p "$VPS_PORT" \
    "${VPS_USER}@${VPS_HOST}" \
    '
set -u

echo "--- HOME ---"
printf "HOME=%s\n" "$HOME"
ls -la "$HOME" 2>/dev/null | head -80

echo
echo "--- COMMON PROJECT LOCATIONS ---"

for p in \
    "$HOME/waste-platform" \
    "$HOME/waste-platform/.production-release" \
    /opt/waste-platform \
    /srv/waste-platform \
    /var/www/waste-platform
do
    if [ -e "$p" ]; then
        echo "FOUND=$p"
        if [ -d "$p/.git" ]; then
            echo "GIT=$p/.git"
        fi
    fi
done

echo
echo "--- LIMITED SEARCH ---"
find "$HOME" /opt /srv /var/www \
    -maxdepth 4 \
    -type d \
    -name "waste-platform" \
    -print 2>/dev/null | head -20
'

echo
echo "============================================================"
echo "4. DOCKER COMPOSE / RELEASE SURFACE"
echo "============================================================"

ssh \
    -p "$VPS_PORT" \
    "${VPS_USER}@${VPS_HOST}" \
    '
set -u

PROJECT=""

for p in \
    "$HOME/waste-platform" \
    /opt/waste-platform \
    /srv/waste-platform \
    /var/www/waste-platform
do
    if [ -d "$p" ]; then
        PROJECT="$p"
        break
    fi
done

if [ -z "$PROJECT" ]; then
    echo "PROJECT=NOT_FOUND"
    exit 0
fi

echo "PROJECT=$PROJECT"

echo
echo "--- PROJECT TOP ---"
find "$PROJECT" -maxdepth 2 -type f \
    \( -name "docker-compose.yml" \
       -o -name "docker-compose.yaml" \
       -o -name "compose.yml" \
       -o -name "compose.yaml" \
       -o -name ".env" \
       -o -name ".env.production" \
       -o -name "deploy.sh" \
    \) \
    -print 2>/dev/null

echo
echo "--- GIT ---"
if [ -d "$PROJECT/.git" ]; then
    echo "GIT=AVAILABLE"
    git -C "$PROJECT" rev-parse --show-toplevel 2>/dev/null || true
    git -C "$PROJECT" rev-parse --short HEAD 2>/dev/null || true
else
    echo "GIT=NOT_FOUND"
fi

echo
echo "--- COMPOSE FILE CONTENT: IMAGE/BUILD ONLY ---"

for f in \
    "$PROJECT/docker-compose.yml" \
    "$PROJECT/docker-compose.yaml" \
    "$PROJECT/compose.yml" \
    "$PROJECT/compose.yaml" \
    "$PROJECT/.production-release/docker-compose.yml"
do
    if [ -f "$f" ]; then
        echo
        echo "FILE=$f"
        grep -nE \
            "^[[:space:]]*(image|build):|REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID|env_file" \
            "$f" 2>/dev/null || true
    fi
done

echo
echo "--- ENVIRONMENT PRESENCE ONLY ---"
for v in REGISTRY_IMAGE_PREFIX IMAGE_TAG RELEASE_ID; do
    if [ -n "${!v:-}" ]; then
        echo "$v=PRESENT"
    else
        echo "$v=ABSENT"
    fi
done

echo
echo "--- RUNNING CONTAINERS ---"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null || true

echo
echo "--- COMPOSE PROJECTS ---"
docker compose ls 2>/dev/null || true
'

echo
echo "============================================================"
echo "PRECHECK FINISHED"
echo "============================================================"
echo "Nothing was deployed."
echo "Nothing was modified."
echo
echo "NEXT:"
echo "Paste the COMPLETE output here."
echo "We will then choose the direct production path from the"
echo "actual VPS state."
