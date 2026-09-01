#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROJECT="$HOME/waste-platform"
WEB="$PROJECT/apps/web"
cd "$WEB"

echo "===== VERSIONS ====="
node -v || true
npm -v || true
npx next --version || true

echo
echo "===== STOP DEV SERVER ====="
pkill -f "next dev" 2>/dev/null || true
sleep 2

echo
echo "===== CLEAN BUILD CACHE ====="
rm -rf .next

echo
echo "===== PRODUCTION BUILD ====="
npm run build > "$HOME/cmep-next-build.log" 2>&1 || true
tail -n 200 "$HOME/cmep-next-build.log" || true

echo
echo "===== START PRODUCTION SERVER ====="
pkill -f "next start" 2>/dev/null || true
nohup npm run start > "$HOME/cmep-next-start.log" 2>&1 &
sleep 8

echo
echo "===== PROD SERVER LOG ====="
tail -n 200 "$HOME/cmep-next-start.log" || true

echo
echo "===== CURL PROD LOCAL ROOT ====="
curl -I --max-time 15 http://127.0.0.1:3001/ || true

echo
echo "===== CURL PROD LOCAL LOGIN ====="
curl -I --max-time 15 http://127.0.0.1:3001/login || true

echo
echo "===== CURL PROD LOCAL BODY LOGIN ====="
curl --max-time 15 http://127.0.0.1:3001/login | head -n 40 || true
