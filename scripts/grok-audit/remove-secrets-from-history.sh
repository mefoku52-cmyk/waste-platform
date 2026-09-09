#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Zaloha pred cistenim historie ==="
BACKUP_BRANCH="backup-before-secret-cleanup-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH"
echo "Zalozena vetva: $BACKUP_BRANCH"

echo ""
echo "=== 2. Kontrola ktore tajomstva su v git ==="
git log --all --full-history -- "*.env" -- "*.pem" -- "*.key" -- "*secret*" 2>/dev/null | head -30

echo ""
echo "=== 3. Odstranenie .env.production z historie ==="
echo "POZOR: Toto prepise git historiu!"
echo "Pokracovat? (napis 'ANO' pre pokracovanie)"
read -r ANSWER
if [ "$ANSWER" != "ANO" ]; then
    echo "Zrusene"
    exit 1
fi

git filter-branch --force \
  --index-filter 'git rm -rf --cached --ignore-unmatch .env.production .env.compose' \
  --prune-empty \
  --tag-name-filter cat \
  -- --all

echo ""
echo "=== 4. Overenie ze .env.production nie je v historii ==="
git log --all --full-history -- ".env.production" 2>/dev/null | head -5 || echo ".env.production uz nie je v git historii"

echo ""
echo "=== 5. Git gc ==="
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "=== 6. Git status ==="
git status --short

echo ""
echo "=== 7. Hotovo ==="
echo "Ak bol repo pushnuty, treba urobit force push:"
echo "  git push origin --force --all"
echo "  git push origin --force --tags"
