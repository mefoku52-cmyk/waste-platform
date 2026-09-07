#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="r76_deployment_active_gate_$(date +%Y%m%d_%H%M%S).txt"

echo "============================================================" | tee "$OUT"
echo "R76 DEPLOYMENT ACTIVE GATE" | tee -a "$OUT"
echo "ROOT=." | tee -a "$OUT"
echo "TIME=$(date -Is)" | tee -a "$OUT"
echo "============================================================" | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== ACTIVE WORKFLOWS ===" | tee -a "$OUT"

WF_COUNT=0

if [ -d .github/workflows ]; then
    while IFS= read -r -d '' f; do
        if grep -qE 'appleboy/(ssh|scp)-action|DEPLOY_HOST|DEPLOY_USER|DEPLOY_PATH|scripts/deploy\.sh' "$f" 2>/dev/null; then
            echo "WORKFLOW=$f" | tee -a "$OUT"
            grep -nE 'appleboy/(ssh|scp)-action|DEPLOY_HOST|DEPLOY_USER|DEPLOY_PATH|scripts/deploy\.sh' "$f" \
                | head -40 \
                | sed -E 's/(DEPLOY_SSH_KEY|[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY))[^[:space:]]*/\1=<REDACTED>/g' \
                | tee -a "$OUT"
            WF_COUNT=$((WF_COUNT+1))
        fi
    done < <(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) -print0)
fi

echo | tee -a "$OUT"
echo "=== DEPLOY SCRIPT ===" | tee -a "$OUT"

DEPLOY_SCRIPT=0

if [ -f scripts/deploy.sh ]; then
    DEPLOY_SCRIPT=1
    echo "FOUND=scripts/deploy.sh" | tee -a "$OUT"

    grep -nE 'REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID|docker (build|push|pull)|docker compose|ssh|scp|rsync' \
        scripts/deploy.sh \
        | head -60 \
        | sed -E 's/(REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID|[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY))=[^[:space:]]+/\1=<REDACTED>/g' \
        | tee -a "$OUT"
else
    echo "FOUND=scripts/deploy.sh NO" | tee -a "$OUT"
fi

echo | tee -a "$OUT"
echo "=== DECISION ===" | tee -a "$OUT"

if [ "$WF_COUNT" -gt 0 ]; then
    echo "VERDICT=ACTIVE_DEPLOYMENT_WORKFLOW_FOUND" | tee -a "$OUT"
elif [ "$DEPLOY_SCRIPT" -eq 1 ]; then
    echo "VERDICT=DEPLOY_SCRIPT_PRESENT_BUT_NO_ACTIVE_WORKFLOW_FOUND" | tee -a "$OUT"
else
    echo "VERDICT=NO_ACTIVE_DEPLOYMENT_PATH_FOUND" | tee -a "$OUT"
fi

echo "WORKFLOW_COUNT=$WF_COUNT" | tee -a "$OUT"
echo "SAFETY=READ_ONLY" | tee -a "$OUT"
echo "SECRETS=NOT_PRINTED" | tee -a "$OUT"
echo "R76 COMPLETE" | tee -a "$OUT"
echo "REPORT=$OUT" | tee -a "$OUT"
