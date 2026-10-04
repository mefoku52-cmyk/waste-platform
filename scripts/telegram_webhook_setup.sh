#!/data/data/com.termux/files/usr/bin/bash
# Registracia Telegram webhooku.
# Pouzitie:
#   TELEGRAM_BOT_TOKEN=xxx \
#   TELEGRAM_WEBHOOK_SECRET=yyy \
#   bash scripts/telegram_webhook_setup.sh https://trc-cmep.sk
#
# Vyzaduje: curl, jq (alebo python3 ako fallback)

set -Eeuo pipefail

WEBHOOK_BASE="${1:-}"
if [ -z "$WEBHOOK_BASE" ]; then
  echo "CHYBA: zadaj base URL (napr. https://trc-cmep.sk)" >&2
  echo "Pouzitie: $0 <BASE_URL>" >&2
  exit 1
fi

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "CHYBA: TELEGRAM_BOT_TOKEN nie je nastaveny" >&2
  exit 1
fi

if [ -z "${TELEGRAM_WEBHOOK_SECRET:-}" ]; then
  echo "CHYBA: TELEGRAM_WEBHOOK_SECRET nie je nastaveny" >&2
  exit 1
fi

if [ ${#TELEGRAM_WEBHOOK_SECRET} -lt 16 ]; then
  echo "CHYBA: WEBHOOK_SECRET musi mat aspon 16 znakov" >&2
  exit 1
fi

WEBHOOK_URL="${WEBHOOK_BASE%/}/api/v1/admin/telegram/webhook"
API="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

echo "=== Registracia webhooku ==="
echo "URL: $WEBHOOK_URL"
echo ""

RESP=$(curl -sS -X POST "${API}/setWebhook" \
  -d "url=${WEBHOOK_URL}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  -d "allowed_updates=[\"message\",\"callback_query\"]" \
  -d "drop_pending_updates=true")

echo "$RESP"
echo ""

# Verify
INFO=$(curl -sS "${API}/getWebhookInfo")
echo "=== Webhook info ==="
echo "$INFO"
