#!/usr/bin/env bash
set -u

echo "============================================================"
echo "R73 - DEPLOYMENT IDENTITY FORENSIC"
echo "============================================================"

echo
echo "--- 1. LOCAL DEPLOYMENT ENVIRONMENT NAMES ONLY ---"
for f in .env .env.production .env.local .env.example; do
    if [ -f "$f" ]; then
        echo "FILE=$f"
        grep -nE '^(DEPLOY_|APP_DOMAIN|API_DOMAIN|PROJECT_DIR|BRANCH|REGISTRY_IMAGE_PREFIX|RELEASE_ID|IMAGE_TAG)=' \
            "$f" 2>/dev/null \
            | sed -E 's/(DEPLOY_SSH_KEY|[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY))=.*/\1=<REDACTED>/'
    fi
done

echo
echo "--- 2. SSH CONFIG HOST NAMES ---"
if [ -f "$HOME/.ssh/config" ]; then
    grep -nE '^[[:space:]]*Host[[:space:]]+' "$HOME/.ssh/config" 2>/dev/null
else
    echo "SSH_CONFIG_NOT_PRESENT"
fi

echo
echo "--- 3. GIT REMOTES ---"
git remote -v 2>/dev/null || true

echo
echo "--- 4. TRACKED DEPLOYMENT IDENTITY REFERENCES ---"
git grep -nEi \
    'DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY|appleboy/(ssh|scp)-action' \
    HEAD -- \
    '.github/workflows/*' \
    'docs/*' \
    'scripts/*' \
    'docker-compose.yml' \
    2>/dev/null || true

echo
echo "--- 5. DEPLOYMENT DOMAIN REFERENCES ---"
git grep -nEi \
    'APP_DOMAIN|API_DOMAIN|server_name|https://|ssh://|scp |rsync ' \
    HEAD -- \
    '.github/workflows/*' \
    'docs/deployment.md' \
    'scripts/deploy.sh' \
    'scripts/bootstrap-letsencrypt.sh' \
    2>/dev/null \
    | head -300 || true

echo
echo "--- 6. HISTORICAL DEPLOYMENT IDENTITY ---"
git log --all --format='%H %ad %s' --date=iso \
    -G'DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY' \
    -- '.github/workflows/*' \
    'docs/*' \
    'scripts/*' \
    2>/dev/null | head -100

echo
echo "--- 7. PUBLIC IP / HOSTNAME HISTORY, REDACTED TO STRUCTURE ---"
git log --all -p -G \
    '([0-9]{1,3}\.){3}[0-9]{1,3}|[A-Za-z0-9.-]+\.(sk|com|net|org)' \
    -- \
    '.github/workflows/*' \
    'docs/deployment.md' \
    'scripts/deploy.sh' \
    'scripts/bootstrap-letsencrypt.sh' \
    2>/dev/null \
    | grep -E \
    '^(commit |Date:|[+-].*((([0-9]{1,3}\.){3}[0-9]{1,3})|[A-Za-z0-9.-]+\.(sk|com|net|org)))' \
    | head -300 || true

echo
echo "--- 8. SAFETY ---"
echo "READ_ONLY=YES"
echo "NO_RUNTIME_EXECUTION=YES"
echo "NO_BUILD=YES"
echo "NO_DEPLOYMENT=YES"
echo "NO_DELETIONS=YES"
echo "NO_SECRET_VALUES_PRINTED=YES"

echo
echo "============================================================"
echo "R73 COMPLETE"
echo "============================================================"
