#!/usr/bin/env bash
set -u

cd ~

echo "=========================================="
echo "ULTIMATE SECRET & CREDENTIAL AUDIT"
echo "=========================================="
echo ""

# Vytvor report adresar
REPORT_DIR="$HOME/secret-audit-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$REPORT_DIR"

echo "=== 1. Hladanie .env suborov ==="
find ~ -maxdepth 6 -name ".env*" -type f 2>/dev/null | tee "$REPORT_DIR/env_files.txt"

echo ""
echo "=== 2. Hladanie suborov s 'password', 'secret', 'token', 'key' v nazve ==="
find ~ -maxdepth 6 -type f ( \
  -iname "*password*" -o \
  -iname "*secret*" -o \
  -iname "*token*" -o \
  -iname "*credential*" -o \
  -iname "*key*" -o \
  -iname "*.pem" -o \
  -iname "*.key" -o \
  -iname "*.p12" -o \
  -iname "*.pfx" \
) 2>/dev/null | tee "$REPORT_DIR/sensitive_files.txt"

echo ""
echo "=== 3. SSH kluce ==="
find ~/.ssh -type f 2>/dev/null | tee "$REPORT_DIR/ssh_keys.txt"

echo ""
echo "=== 4. Git tajomstva (git config, credentials) ==="
find ~ -maxdepth 6 -name ".git-credentials" -o -name ".gitconfig" 2>/dev/null | tee "$REPORT_DIR/git_secrets.txt"

echo ""
echo "=== 5. Databazove súbory ==="
find ~ -maxdepth 6 -type f ( \
  -name "*.db" -o \
  -name "*.sqlite" -o \
  -name "*.sqlite3" \
) 2>/dev/null | tee "$REPORT_DIR/databases.txt"

echo ""
echo "=== 6. Vypis obsahu .env suborov (BEZPECNE - len nazvy premennych) ==="
for envfile in $(cat "$REPORT_DIR/env_files.txt"); do
    echo "--- $envfile ---"
    grep -v "^#" "$envfile" 2>/dev/null | cut -d'=' -f1 | sed 's/=.*/=***REDACTED***/' || echo "NECITATELNY"
done | tee "$REPORT_DIR/env_variables.txt"

echo ""
echo "=== 7. Hladanie hardcoded hesiel v Python a JS suboroch ==="
grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.tsx" \
  -e "passwords*=s*['"]" \
  -e "PASSWORDs*=s*['"]" \
  -e "secrets*=s*['"]" \
  -e "SECRETs*=s*['"]" \
  -e "api_keys*=s*['"]" \
  -e "API_KEYs*=s*['"]" \
  ~/waste-platform/app 2>/dev/null | head -50 | tee "$REPORT_DIR/hardcoded_secrets.txt"

echo ""
echo "=== 8. Waste-platform specificke tajomstva ==="
echo "--- .env vo waste-platform ---"
cat ~/waste-platform/.env 2>/dev/null | grep -v "^#" | sed 's/=(.*)/=***\u0001***/' || echo "Nenajdene"

echo ""
echo "--- Databazove URL ---"
grep -r "DATABASE_URL" ~/waste-platform/.env* 2>/dev/null | sed 's/=(.*)/=***\u0001***/' || echo "Nenajdene"

echo ""
echo "=== 9. Celkovy sucet ==="
echo "ENV suborov: $(wc -l < "$REPORT_DIR/env_files.txt")"
echo "Citlivych suborov: $(wc -l < "$REPORT_DIR/sensitive_files.txt")"
echo "SSH klucov: $(wc -l < "$REPORT_DIR/ssh_keys.txt")"
echo "Git tajomstiev: $(wc -l < "$REPORT_DIR/git_secrets.txt")"
echo "Databaz: $(wc -l < "$REPORT_DIR/databases.txt")"

echo ""
echo "=== 10. Report ulozeny v: $REPORT_DIR ==="
echo "=========================================="
