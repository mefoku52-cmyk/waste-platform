#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# CMEP - Secret Rotation Script
# =============================================================================
# Rotates the ONLY self-generated secret this app owns: JWT_SECRET_KEY.
# Provider-side secrets (Stripe, Resend/SMTP, Groq, Mistral, Cerebras,
# Deepgram, Telegram bot token, GitHub) CANNOT be rotated by this script --
# they must be regenerated at the provider and then updated in the environment.
# The script never prints secret values.
#
# Usage:
#   bash scripts/security/rotate-secrets.sh [env_file] [--dry-run]
#
#   env_file   path to the env file (default: .env.production)
#   --dry-run  validate and show the plan WITHOUT changing anything
# =============================================================================

set -Eeuo pipefail

ENV_FILE=""
DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --help|-h)
            grep '^#' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) ENV_FILE="$arg" ;;
    esac
done
ENV_FILE="${ENV_FILE:-.env.production}"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: subor '$ENV_FILE' neexistuje. Zadaj cestu k env suboru."
    exit 1
fi

if ! grep -q '^JWT_SECRET_KEY=' "$ENV_FILE"; then
    echo "ERROR: '$ENV_FILE' neobsahuje JWT_SECRET_KEY. Nic sa nemeni."
    exit 1
fi

mask() {
    # Show only length, never the value.
    printf '(%d znakov, skryte)' "${#1}"
}

gen_secret() {
    python3 -c "import secrets, string; alphabet = string.ascii_letters + string.digits; print(''.join(secrets.choice(alphabet) for _ in range(${1:-64})))"
}

NEW_JWT_SECRET="$(gen_secret 64)"

echo "Rotacia sekretov: $ENV_FILE"
echo "JWT_SECRET_KEY -> $(mask "$NEW_JWT_SECRET")"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY-RUN: nic sa nezmenilo. Bez --dry-run by sa spravila zaloha a prepis JWT_SECRET_KEY."
    exit 0
fi

BACKUP_DIR="logs/backups/secrets-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp "$ENV_FILE" "$BACKUP_DIR/$(basename "$ENV_FILE").bak"
chmod 600 "$BACKUP_DIR/$(basename "$ENV_FILE").bak" 2>/dev/null || true
echo "Zaloha: $BACKUP_DIR/"

tmp="$(mktemp)"
sed "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$NEW_JWT_SECRET|" "$ENV_FILE" > "$tmp"
mv "$tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE" 2>/dev/null || true

echo "JWT_SECRET_KEY zrotovany."
echo ""
echo "DALSIE KROKY (manualne, mimo tohto skriptu):"
echo "  1. Zrotuj poskytovatelske kluce PRI POSKYTOVATELI: Stripe, Resend/SMTP,"
echo "     Groq, Mistral, Cerebras, Deepgram, Telegram bot token, GitHub."
echo "  2. Aktualizuj ich v prostredi (Render env / docker secrets), nikdy v gite."
echo "  3. Restartuj sluzby."
echo "  4. Over: make audit-security (alebo bash scripts/security/audit.sh)."
echo "  5. Po overeni zmaz zalohu: rm -rf $BACKUP_DIR"
