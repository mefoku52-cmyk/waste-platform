#!/usr/bin/env bash
set -u

cd ~

echo "=========================================="
echo "ULTIMATE SECRET & CREDENTIAL AUDIT V2"
echo "=========================================="
echo ""

REPORT_DIR="$HOME/secret-audit-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$REPORT_DIR"

echo "=== 1. Hladanie .env suborov ==="
find ~ -maxdepth 6 -name ".env*" -type f 2>/dev/null | tee "$REPORT_DIR/env_files.txt"

echo ""
echo "=== 2. Hladanie citlivych suborov ==="
find ~ -maxdepth 6 -type f -name "*password*" 2>/dev/null > "$REPORT_DIR/password_files.txt"
find ~ -maxdepth 6 -type f -name "*secret*" 2>/dev/null >> "$REPORT_DIR/password_files.txt"
find ~ -maxdepth 6 -type f -name "*token*" 2>/dev/null >> "$REPORT_DIR/password_files.txt"
find ~ -maxdepth 6 -type f -name "*credential*" 2>/dev/null >> "$REPORT_DIR/password_files.txt"
find ~ -maxdepth 6 -type f -name "*key*" 2>/dev/null >> "$REPORT_DIR/password_files.txt"
find ~ -maxdepth 6 -type f -name "*.pem" 2>/dev/null >> "$REPORT_DIR/password_files.txt"
find ~ -maxdepth 6 -type f -name "*.key" 2>/dev/null >> "$REPORT_DIR/password_files.txt"
cat "$REPORT_DIR/password_files.txt" | sort -u | tee "$REPORT_DIR/sensitive_files.txt"

echo ""
echo "=== 3. SSH kluce ==="
find ~/.ssh -type f 2>/dev/null | tee "$REPORT_DIR/ssh_keys.txt"

echo ""
echo "=== 4. Git tajomstva ==="
find ~ -maxdepth 6 -name ".git-credentials" -o -name ".gitconfig" 2>/dev/null | tee "$REPORT_DIR/git_secrets.txt"

echo ""
echo "=== 5. Databazove subory ==="
find ~ -maxdepth 6 -type f -name "*.db" 2>/dev/null > "$REPORT_DIR/databases.txt"
find ~ -maxdepth 6 -type f -name "*.sqlite" 2>/dev/null >> "$REPORT_DIR/databases.txt"
find ~ -maxdepth 6 -type f -name "*.sqlite3" 2>/dev/null >> "$REPORT_DIR/databases.txt"
cat "$REPORT_DIR/databases.txt" | tee "$REPORT_DIR/databases_sorted.txt"

echo ""
echo "=== 6. Vypis .env premennych (BEZ HODNOT) ==="
for envfile in $(cat "$REPORT_DIR/env_files.txt" | head -20); do
    echo "--- $envfile ---"
    grep -v "^#" "$envfile" 2>/dev/null | cut -d'=' -f1 | sed 's/$/=***/' || echo "NECITATELNY"
done | tee "$REPORT_DIR/env_variables.txt"

echo ""
echo "=== 7. Hladanie hardcoded hesiel v kode ==="
grep -rn --include="*.py" --include="*.js" --include="*.ts" \
  -e "passwords*=" \
  -e "PASSWORDs*=" \
  -e "secrets*=" \
  -e "SECRETs*=" \
  -e "api_keys*=" \
  -e "API_KEYs*=" \
  ~/waste-platform/app 2>/dev/null | head -50 | tee "$REPORT_DIR/hardcoded_secrets.txt"

echo ""
echo "=== 8. Waste-platform .env ==="
cat ~/waste-platform/.env 2>/dev/null | grep -v "^#" | sed 's/=(.*)/=***/' || echo "Nenajdene"

echo ""
echo "=== 9. Celkovy sucet ==="
echo "ENV suborov: $(wc -l < "$REPORT_DIR/env_files.txt")"
echo "Citlivych suborov: $(wc -l < "$REPORT_DIR/sensitive_files.txt")"
echo "SSH klucov: $(wc -l < "$REPORT_DIR/ssh_keys.txt")"
echo "Git tajomstiev: $(wc -l < "$REPORT_DIR/git_secrets.txt")"
echo "Databaz: $(wc -l < "$REPORT_DIR/databases_sorted.txt")"

echo ""
echo "=== 10. Report ulozeny v: $REPORT_DIR ==="
echo "=========================================="
