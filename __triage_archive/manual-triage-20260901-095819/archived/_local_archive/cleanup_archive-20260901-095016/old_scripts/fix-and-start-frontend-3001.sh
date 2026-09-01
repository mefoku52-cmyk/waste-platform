#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROJECT="$HOME/waste-platform"
WEB="$PROJECT/apps/web"

cd "$WEB"

echo "===== BACKUP ====="
mkdir -p "$HOME/waste-platform-backups"
cp -av package.json "$HOME/waste-platform-backups/package.json.$(date +%Y%m%d_%H%M%S).bak"
cp -av .env.local "$HOME/waste-platform-backups/web.env.local.$(date +%Y%m%d_%H%M%S).bak" 2>/dev/null || true
cp -av fix_everything.sh "$HOME/waste-platform-backups/fix_everything.sh.$(date +%Y%m%d_%H%M%S).bak" 2>/dev/null || true

HOST_IP="$(ip addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1)"
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
fi
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="192.168.1.200"
fi

echo "===== HOST IP ====="
echo "$HOST_IP"

echo "===== FIX .env.local ====="
cat > .env.local <<ENVEOF
NEXT_PUBLIC_API_BASE_URL=http://$HOST_IP:8001/api/v1
ENVEOF

echo "===== FIX package.json scripts to bind 0.0.0.0 ====="
python - <<'PY'
import json
from pathlib import Path

p = Path("package.json")
data = json.loads(p.read_text(encoding="utf-8"))

scripts = data.setdefault("scripts", {})
if scripts.get("dev") == "next dev --port 3001":
    scripts["dev"] = "next dev --hostname 0.0.0.0 --port 3001"
elif "next dev" in scripts.get("dev", "") and "--hostname" not in scripts.get("dev", ""):
    scripts["dev"] = scripts["dev"].replace("next dev", "next dev --hostname 0.0.0.0")

if scripts.get("start") == "next start --port 3001":
    scripts["start"] = "next start --hostname 0.0.0.0 --port 3001"
elif "next start" in scripts.get("start", "") and "--hostname" not in scripts.get("start", ""):
    scripts["start"] = scripts["start"].replace("next start", "next start --hostname 0.0.0.0")

p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

echo "===== FIX stale helper script ====="
python - <<'PY'
from pathlib import Path
p = Path("fix_everything.sh")
if p.exists():
    text = p.read_text(encoding="utf-8")
    text = text.replace("NEXT_PUBLIC_API_BASE_URL=http://localhost:8001", "NEXT_PUBLIC_API_BASE_URL=http://192.168.1.200:8001/api/v1")
    p.write_text(text, encoding="utf-8")
PY

echo "===== REMOVE OLD BUILD CACHE ====="
rm -rf .next

echo "===== INSTALL NODE MODULES IF NEEDED ====="
[ -d node_modules ] || npm install

echo "===== SHOW ACTIVE CONFIG ====="
grep -n "NEXT_PUBLIC_API_BASE_URL" .env.local || true
sed -n '1,120p' package.json

echo "===== START FRONTEND ====="
pkill -f "next dev" 2>/dev/null || true
nohup npm run dev > "$HOME/cmep-frontend-3001.log" 2>&1 &

sleep 8

echo "===== FRONTEND LOG TAIL ====="
tail -n 120 "$HOME/cmep-frontend-3001.log" || true

echo
echo "OPEN THIS URL:"
echo "http://$HOST_IP:3001/login"
