#!/data/data/com.termux/files/usr/bin/bash
set -eu

WEB="$HOME/waste-platform/apps/web"
cd "$WEB"

echo "===== FIND NEXT CONFIG ====="
ls -1 next.config.* 2>/dev/null || true

echo "===== BACKUP ====="
mkdir -p "$HOME/waste-platform-backups"
[ -f next.config.js ] && cp -av next.config.js "$HOME/waste-platform-backups/next.config.js.$(date +%Y%m%d_%H%M%S).bak" || true
[ -f next.config.mjs ] && cp -av next.config.mjs "$HOME/waste-platform-backups/next.config.mjs.$(date +%Y%m%d_%H%M%S).bak" || true
[ -f next.config.ts ] && cp -av next.config.ts "$HOME/waste-platform-backups/next.config.ts.$(date +%Y%m%d_%H%M%S).bak" || true

echo "===== WRITE TERMUX-SAFE next.config.mjs ====="
cat > next.config.mjs <<'CFG'
/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: false,
  },
  outputFileTracing: false,
}

export default nextConfig
CFG

echo "===== CLEAN ====="
rm -rf .next

echo "===== BUILD ====="
npm run build > "$HOME/cmep-next-build-after-tracing-fix.log" 2>&1 || true
tail -n 200 "$HOME/cmep-next-build-after-tracing-fix.log" || true

echo
echo "===== START PROD ====="
pkill -f "next start" 2>/dev/null || true
nohup npm run start > "$HOME/cmep-next-start-after-tracing-fix.log" 2>&1 &
sleep 8
tail -n 200 "$HOME/cmep-next-start-after-tracing-fix.log" || true

echo
echo "===== CURL LOCAL LOGIN ====="
curl -I --max-time 15 http://127.0.0.1:3001/login || true
curl --max-time 15 http://127.0.0.1:3001/login | head -n 40 || true
