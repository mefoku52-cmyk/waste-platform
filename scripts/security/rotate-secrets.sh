#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# CMEP — Secret Rotation Script
# =============================================================================
# Pouzitie: bash scripts/security/rotate-secrets.sh [environment]
# =============================================================================

set -euo pipefail

ENV_FILE="${1:-.env.production}"
BACKUP_DIR="logs/backups/secrets-$(date +%Y%m%d-%H%M%S)"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Subor $ENV_FILE neexistuje!"
    exit 1
fi

echo "🔐 Rotacia sekretov: $ENV_FILE"
mkdir -p "$BACKUP_DIR"
cp "$ENV_FILE" "$BACKUP_DIR/$(basename $ENV_FILE).bak"
echo "✅ Zaloha: $BACKUP_DIR/"

# Funkcia na generovanie secretu
gen_secret() {
    python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*-_+=') for _ in range(${1:-64})))"
}

# Rotacia
echo ""
echo "Generujem nove secrety..."

NEW_JWT_SECRET=$(gen_secret 64)
NEW_JWT_REFRESH=$(gen_secret 64)
NEW_POSTGRES_PASS=$(gen_secret 32)
NEW_MINIO_PASS=$(gen_secret 32)
NEW_GRAFANA_PASS=$(gen_secret 16)

# Pouzijeme sed na nahradenie (opatrne!)
sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$NEW_JWT_SECRET|" "$ENV_FILE"
sed -i "s|^JWT_REFRESH_SECRET_KEY=.*|JWT_REFRESH_SECRET_KEY=$NEW_JWT_REFRESH|" "$ENV_FILE"
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$NEW_POSTGRES_PASS|" "$ENV_FILE"
sed -i "s|^MINIO_ROOT_PASSWORD=.*|MINIO_ROOT_PASSWORD=$NEW_MINIO_PASS|" "$ENV_FILE"
sed -i "s|^GRAFANA_PASSWORD=.*|GRAFANA_PASSWORD=$NEW_GRAFANA_PASS|" "$ENV_FILE"

echo "✅ Secrety zrotovane!"
echo ""
echo "⚠️  DALSIE KROKY:"
echo "   1. Restartuj sluzby: make down && make up"
echo "   2. Over funkcnost: make audit-security"
echo "   3. Zmaz zalohu po overeni: rm -rf $BACKUP_DIR"
echo ""
echo "📋 Zaloha sekretov: $BACKUP_DIR/"
