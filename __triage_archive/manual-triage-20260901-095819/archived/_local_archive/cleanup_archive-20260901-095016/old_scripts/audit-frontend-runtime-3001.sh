#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROJECT="$HOME/waste-platform"
WEB="$PROJECT/apps/web"
cd "$WEB"

HOST_IP="$(ip addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1)"
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
fi
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="192.168.1.200"
fi

echo "===== HOST IP ====="
echo "$HOST_IP"

echo
echo "===== NODE/NEXT PROCESSES ====="
ps -ef | grep -E 'next dev|node' | grep -v grep || true

echo
echo "===== CURL LOCAL FRONTEND ROOT ====="
curl -I --max-time 10 http://127.0.0.1:3001/ || true

echo
echo "===== CURL LOCAL FRONTEND LOGIN ====="
curl -I --max-time 10 http://127.0.0.1:3001/login || true

echo
echo "===== CURL LAN FRONTEND ROOT ====="
curl -I --max-time 10 "http://$HOST_IP:3001/" || true

echo
echo "===== CURL LAN FRONTEND LOGIN ====="
curl -I --max-time 10 "http://$HOST_IP:3001/login" || true

echo
echo "===== BACKEND HEALTH ====="
curl -I --max-time 10 http://127.0.0.1:8001/health || true

echo
echo "===== FRONTEND LOG FULL TAIL ====="
tail -n 200 "$HOME/cmep-frontend-3001.log" || true

echo
echo "===== TRY BUILD ====="
npm run build > "$HOME/cmep-frontend-build.log" 2>&1 || true
tail -n 200 "$HOME/cmep-frontend-build.log" || true
