#!/usr/bin/env bash
set -u

echo "=== 1. Odstranenie API tokenov z home ==="
rm -f ~/.gemini_token ~/.grok_token ~/.openai_token 2>/dev/null && echo "API tokeny odstranene" || echo "Tokeny nenajdene"

echo ""
echo "=== 2. Skontroluj .gitignore ==="
cat ~/waste-platform/.gitignore 2>/dev/null | grep -E "^.env|token|secret|key" || echo "POZOR: .env nie je v gitignore!"

echo ""
echo "=== 3. Vytvor bezpecny .gitignore ==="
cat >> ~/waste-platform/.gitignore <<'GITIGNORE'
# Tajomstvá
.env
.env.*
!.env.example
*.key
*.pem
*.p12
*.pfx
*.keystore
*_secret*.json
secret*.env
secrets*.env
.token
*_token
token*.txt

# SSH
.ssh/
.gnupg/

# Backupy s tajomstvami
.env.backup*
.env.bak*
.env.*bak
GITIGNORE

echo ""
echo "=== 4. Skontroluj git status ==="
cd ~/waste-platform
git status --short | grep -E ".env|token|secret|key" || echo "Ziadne tajomstva v git"

echo ""
echo "=== 5. Odstran tajomstva z git history (ak su) ==="
echo "POZOR: Toto je destruktivna operacia - zalohuj si repo!"
echo "git filter-branch --force --index-filter 'git rm -rf --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all"
