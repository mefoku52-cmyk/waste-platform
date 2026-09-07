#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="${1:-.}"
OUT="r75_deployment_identity_$(date +%Y%m%d_%H%M%S).txt"

PATTERN='DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY|VPS_HOST|VPS_USER|VPS_PORT|SERVER_HOST|SERVER_IP|PRODUCTION_HOST|PROD_HOST|REGISTRY_IMAGE_PREFIX|appleboy/(ssh|scp)-action'

echo "============================================================" | tee "$OUT"
echo "R75 DEPLOYMENT IDENTITY DECISION AUDIT" | tee -a "$OUT"
echo "ROOT=$ROOT" | tee -a "$OUT"
echo "TIME=$(date -Is)" | tee -a "$OUT"
echo "============================================================" | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 1. ACTIVE PROJECT SOURCES ===" | tee -a "$OUT"

grep -RInE \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=.git \
  --exclude-dir=_quarantine \
  --exclude-dir=archive \
  --exclude='*.map' \
  "$PATTERN" "$ROOT" 2>/dev/null \
| sed -E \
  's/(DEPLOY_SSH_KEY|[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY))=[^[:space:]]+/\1=<REDACTED>/g' \
| head -200 \
| tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 2. CI/CD WORKFLOWS ===" | tee -a "$OUT"

find "$ROOT/.github/workflows" -type f 2>/dev/null \
| while read -r f; do
    grep -nE \
      'appleboy/(ssh|scp)-action|DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY' \
      "$f" 2>/dev/null \
    && echo "FILE=$f"
  done \
| head -100 \
| tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 3. DEPLOYMENT SCRIPTS ===" | tee -a "$OUT"

find "$ROOT/scripts" -maxdepth 2 -type f 2>/dev/null \
| while read -r f; do
    grep -IlE \
      'DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY|ssh |scp |rsync ' \
      "$f" 2>/dev/null \
    && echo "  -> $f"
  done \
| head -100 \
| tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 4. GIT HISTORY SIGNAL ===" | tee -a "$OUT"

git -C "$ROOT" log --all --oneline -G \
  'DEPLOY_HOST|DEPLOY_USER|DEPLOY_PORT|DEPLOY_PATH|DEPLOY_SSH_KEY|appleboy/(ssh|scp)-action' \
  -- '.github/workflows/*' 'scripts/*' 'docs/*' 'docker-compose.yml' \
  2>/dev/null \
| head -50 \
| tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 5. DECISION ===" | tee -a "$OUT"

ACTIVE=$(grep -RIlE \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=.git \
  --exclude-dir=_quarantine \
  --exclude-dir=archive \
  'appleboy/(ssh|scp)-action|DEPLOY_HOST|DEPLOY_USER|DEPLOY_PATH|DEPLOY_SSH_KEY' \
  "$ROOT/.github" "$ROOT/scripts" 2>/dev/null | wc -l)

DOCS=$(grep -RIlE \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=.git \
  'DEPLOY_HOST|DEPLOY_USER|DEPLOY_PATH|DEPLOY_SSH_KEY' \
  "$ROOT/docs" 2>/dev/null | wc -l)

if [ "$ACTIVE" -gt 0 ]; then
    echo "VERDICT=DEPLOYMENT_IDENTITY_PRESENT_IN_ACTIVE_PROJECT" | tee -a "$OUT"
    echo "ACTIVE_FILES=$ACTIVE" | tee -a "$OUT"
elif [ "$DOCS" -gt 0 ]; then
    echo "VERDICT=DEPLOYMENT_IDENTITY_DOCUMENTED_ONLY" | tee -a "$OUT"
    echo "DOC_FILES=$DOCS" | tee -a "$OUT"
else
    echo "VERDICT=NO_DEPLOYMENT_IDENTITY_FOUND_IN_ACTIVE_PROJECT" | tee -a "$OUT"
fi

echo | tee -a "$OUT"
echo "SAFETY=READ_ONLY" | tee -a "$OUT"
echo "SECRETS=NOT_PRINTED" | tee -a "$OUT"
echo "R75 COMPLETE" | tee -a "$OUT"
echo "REPORT=$OUT" | tee -a "$OUT"
