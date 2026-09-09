#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Kontrola ci .env nie je v git history ==="
git log --all --full-history -- ".env" 2>/dev/null | head -5 || echo ".env nie je v git history"

echo ""
echo "=== 2. Kontrola ci .env.production nie je v git ==="
git log --all --full-history -- ".env.production" 2>/dev/null | head -5 || echo ".env.production nie je v git history"

echo ""
echo "=== 3. Opravnenia na citlive subory ==="
chmod 600 ~/.ssh/id_ed25519 ~/.ssh/id_rsa 2>/dev/null && echo "SSH kluce: chmod 600 OK" || echo "SSH kluce nenajdene"
chmod 600 ~/.ssh/authorized_keys 2>/dev/null && echo "authorized_keys: chmod 600 OK" || echo "authorized_keys nenajdene"
chmod 600 ~/waste-platform/.env 2>/dev/null && echo ".env: chmod 600 OK" || echo ".env nenajdene"
chmod 600 ~/waste-platform/.env.production 2>/dev/null && echo ".env.production: chmod 600 OK" || echo ".env.production nenajdene"

echo ""
echo "=== 4. Zaloha tajomstiev ==="
BACKUP_DIR="$HOME/.secure-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp ~/.ssh/id_ed25519 "$BACKUP_DIR/" 2>/dev/null
cp ~/.ssh/id_rsa "$BACKUP_DIR/" 2>/dev/null
cp ~/waste-platform/.env "$BACKUP_DIR/" 2>/dev/null
cp ~/waste-platform/.env.production "$BACKUP_DIR/" 2>/dev/null

chmod 700 "$BACKUP_DIR"
chmod 600 "$BACKUP_DIR"/*

echo "Zaloha vytvorena: $BACKUP_DIR"
ls -la "$BACKUP_DIR"

echo ""
echo "=== 5. Vymazanie backupov s tajomstvami z downloads ==="
rm -rf ~/downloads/waste-platform-fix-web-build-admin-user-type/.env* 2>/dev/null && echo "Backup .env z downloads odstraneny" || echo "Nenajdene"

echo ""
echo "=== 6. Zoznam tajomstiev na rotaciu ==="
echo "POZOR: Tieto tajomstva treba rotovat (vymenit za nove):"
echo "  - API tokeny (Gemini, Grok, OpenAI) - UZ odstranene"
echo "  - SSH kluce (ak boli kompromitovane)"
echo "  - DATABASE_URL v .env"
echo "  - JWT_SECRET v .env"
echo "  - Vsetky .env.production tajomstva"

echo ""
echo "=== 7. Hotovo ==="
echo "Report ulozeny v: $BACKUP_DIR"
