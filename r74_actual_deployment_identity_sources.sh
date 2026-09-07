#!/usr/bin/env bash
set -u

echo "============================================================"
echo "R74 - ACTUAL DEPLOYMENT IDENTITY SOURCES"
echo "============================================================"

echo
echo "--- 1. GITHUB CLI AVAILABILITY ---"
if command -v gh >/dev/null 2>&1; then
    echo "GH_PRESENT=YES"
    gh --version 2>/dev/null | head -1 || true
else
    echo "GH_PRESENT=NO"
fi

echo
echo "--- 2. GITHUB CLI CONFIG STRUCTURE ---"
if [ -d "$HOME/.config/gh" ]; then
    find "$HOME/.config/gh" -maxdepth 2 -type f -print 2>/dev/null \
        | sed 's#^#GH_CONFIG_FILE=#'
else
    echo "GH_CONFIG_NOT_PRESENT"
fi

echo
echo "--- 3. SHELL HISTORY DEPLOYMENT REFERENCES ---"
for f in \
    "$HOME/.bash_history" \
    "$HOME/.zsh_history" \
    "$HOME/.termux/shell-history" \
    "$HOME/.config/fish/fish_history"
do
    if [ -f "$f" ]; then
        echo "HISTORY_FILE=$f"

        grep -nEi \
            'DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY|ssh |scp |rsync |appleboy|github.*secret|gh secret|docker.*login|docker.*push' \
            "$f" 2>/dev/null \
            | sed -E \
              's/(DEPLOY_SSH_KEY|[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY))=[^[:space:]]+/\1=<REDACTED>/g' \
            | head -300
    fi
done

echo
echo "--- 4. LOCAL ENVIRONMENT VARIABLE NAMES ONLY ---"
env | cut -d= -f1 \
    | grep -E \
      '^(DEPLOY_|GITHUB_|GH_|APP_DOMAIN|API_DOMAIN|PROJECT_DIR|REGISTRY_|RELEASE_ID|IMAGE_TAG)' \
    | sort

echo
echo "--- 5. GIT CONFIG ---"
git config --local --get-regexp \
    'remote\.|branch\.|deploy|host|server|url' \
    2>/dev/null \
    | sed -E \
      's#(https?://)[^/@]+@#\1<REDACTED>@#g'

echo
echo "--- 6. ALL LOCAL GIT REMOTES ---"
git remote -v 2>/dev/null || true

echo
echo "--- 7. DEPLOYMENT-RELATED FILE NAMES ---"
find . \
    -type f \
    \( \
      -iname '*deploy*' \
      -o -iname '*release*' \
      -o -iname '*vps*' \
      -o -iname '*server*' \
      -o -iname '*infra*' \
      -o -iname '*ssh*' \
    \) \
    -not -path './.git/*' \
    -not -path './node_modules/*' \
    2>/dev/null \
    | head -500

echo
echo "--- 8. LOCAL SSH MATERIAL STRUCTURE ONLY ---"
if [ -d "$HOME/.ssh" ]; then
    find "$HOME/.ssh" -maxdepth 2 -type f -printf '%f\n' 2>/dev/null \
        | sed -E \
          's/(id_[^.]*(\.pub)?|.*known_hosts.*|.*authorized_keys.*)/<SSH_FILE>/'
else
    echo "SSH_DIR_NOT_PRESENT"
fi

echo
echo "--- 9. PROJECT-WIDE DEPLOYMENT IDENTITY TOKENS ---"
grep -RniE \
    'DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY|appleboy/(ssh|scp)-action|ssh[[:space:]].*@|scp[[:space:]].*@|rsync[[:space:]].*@' \
    . \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude='package-lock.json' \
    2>/dev/null \
    | sed -E \
      's/(DEPLOY_SSH_KEY|[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY))=[^[:space:]]+/\1=<REDACTED>/g' \
    | head -500

echo
echo "--- 10. SAFETY ---"
echo "READ_ONLY=YES"
echo "NO_RUNTIME_EXECUTION=YES"
echo "NO_BUILD=YES"
echo "NO_DEPLOYMENT=YES"
echo "NO_DELETIONS=YES"
echo "NO_SECRET_VALUES_PRINTED=YES"

echo
echo "============================================================"
echo "R74 COMPLETE"
echo "============================================================"
