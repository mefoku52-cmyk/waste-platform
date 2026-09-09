#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

cd "$HOME/waste-platform"

PASS=0
FAIL=0
WARN=0

pass() { PASS=$((PASS+1)); printf '[PASS] %s\n' "$1"; }
fail() { FAIL=$((FAIL+1)); printf '[FAIL] %s\n' "$1"; }
warn() { WARN=$((WARN+1)); printf '[WARN] %s\n' "$1"; }

echo "============================================================"
echo "PHASE 3 - RUNTIME SECRETS AUTHORITY AUDIT"
echo "============================================================"

echo
echo "=== 1. REQUIRED COMPOSE VARIABLES ==="

grep -RhoE '\$\{[A-Z0-9_]+(:-[^}]*)?(:\?[^}]*)?\}' \
  docker-compose.yml \
  2>/dev/null \
  | sed -E 's/^\$\{//; s/(:-[^}]*)?$//; s/(:\?[^}]*)?$//' \
  | sort -u \
  | while read -r v; do
      printf 'COMPOSE_VAR=%s\n' "$v"
    done

echo
echo "=== 2. REQUIRED SECRET NAMES IN COMPOSE ==="

grep -nE \
  'POSTGRES_PASSWORD|JWT_REFRESH_SECRET_KEY|SECRET|PASSWORD|TOKEN|API_KEY' \
  docker-compose.yml \
  2>/dev/null \
  | sed -E \
    's/(=.*)$/=***REDACTED***/; s/(password: ).*$/\1***REDACTED***/' \
  || true

echo
echo "=== 3. .env.production VARIABLE NAMES ==="

if [ -f .env.production ]; then
  sed -nE 's/^([A-Z][A-Z0-9_]*)=.*/\1=<PRESENT>/p' \
    .env.production \
    | sort
  pass ".env.production exists"
else
  warn ".env.production does not exist"
fi

echo
echo "=== 4. REQUIRED VARIABLES IN .env.production ==="

for key in POSTGRES_PASSWORD JWT_REFRESH_SECRET_KEY REGISTRY_IMAGE_PREFIX IMAGE_TAG RELEASE_ID; do
  if grep -qE "^${key}=" .env.production 2>/dev/null; then
    value="$(grep -E "^${key}=" .env.production | head -1 | cut -d= -f2-)"
    if [ -n "$value" ]; then
      pass "$key exists and is non-empty in .env.production"
    else
      fail "$key exists but is empty in .env.production"
    fi
  else
    warn "$key is missing from .env.production"
  fi
done

echo
echo "=== 5. CURRENT SHELL ENVIRONMENT ==="

for key in POSTGRES_PASSWORD JWT_REFRESH_SECRET_KEY REGISTRY_IMAGE_PREFIX IMAGE_TAG RELEASE_ID; do
  if [ -n "${!key:-}" ]; then
    pass "$key exists in current shell environment"
  else
    echo "[INFO] $key not present in current shell"
  fi
done

echo
echo "=== 6. DEPLOY SCRIPT SECRET HANDLING ==="

echo "--- relevant deploy.sh lines ---"

grep -nE \
  'POSTGRES_PASSWORD|JWT_REFRESH_SECRET_KEY|\.env|--env-file|RELEASE_ID|IMAGE_TAG|REGISTRY_IMAGE_PREFIX' \
  scripts/deploy.sh \
  2>/dev/null \
  | sed -E \
    's/(POSTGRES_PASSWORD=).*/\1***REDACTED***/;
     s/(JWT_REFRESH_SECRET_KEY=).*/\1***REDACTED***/' \
  || true

echo
echo "=== 7. ENV FILE INVENTORY ==="

find . \
  -maxdepth 3 \
  -type f \
  \( -name '.env' -o -name '.env.*' \) \
  -not -path './node_modules/*' \
  -not -path './.git/*' \
  -print \
  2>/dev/null \
  | sort

echo
echo "=== 8. GIT TRACKING SAFETY ==="

for f in .env .env.production .env.local; do
  if [ -f "$f" ]; then
    if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      fail "$f is tracked by Git"
    else
      pass "$f is not tracked by Git"
    fi
  fi
done

echo
echo "=== 9. GITIGNORE SECRET PROTECTION ==="

grep -nE \
  '^\.env$|^\.env\*|^\.env\..*|env\.production|secret' \
  .gitignore \
  2>/dev/null \
  || warn "No obvious env protection rule found in .gitignore"

echo
echo "=== 10. GITHUB ACTIONS SECRETS NAMES ==="

gh secret list \
  --repo mefoku52-cmyk/waste-platform \
  2>/dev/null \
  | awk '{print $1}' \
  | sort \
  || warn "Unable to list GitHub Actions secret names"

echo
echo "=== 11. SECRET REFERENCES IN SOURCE ==="

grep -RniE \
  'POSTGRES_PASSWORD|JWT_REFRESH_SECRET_KEY' \
  app apps scripts docker-compose.yml \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  2>/dev/null \
  | head -100 \
  | sed -E \
    's/(POSTGRES_PASSWORD[=: ]+).*/\1***REDACTED***/;
     s/(JWT_REFRESH_SECRET_KEY[=: ]+).*/\1***REDACTED***/' \
  || true

echo
echo "============================================================"
echo "PHASE 3 RESULT"
echo "============================================================"
echo "PASS=$PASS"
echo "FAIL=$FAIL"
echo "WARN=$WARN"

if [ "$FAIL" -eq 0 ]; then
  echo "PHASE3_VERDICT=PASS"
else
  echo "PHASE3_VERDICT=FAIL"
fi

echo
echo "IMPORTANT=NO_SECRET_VALUES_WERE_PRINTED"
echo "IMPORTANT=NO_DEPLOY_WAS_PERFORMED"
