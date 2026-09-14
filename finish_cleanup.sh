#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

echo "==============================================="
echo " 1. Oprava UTC importu v 2 súboroch"
echo "==============================================="
python - <<'PY'
files = [
    "app/modules/inquiries/application/services.py",
    "app/modules/listings/application/services.py",
]
for p in files:
    s = open(p).read()
    # Ak je lokálny import bez UTC, doplň ho
    if "from datetime import UTC" in s:
        print(f"[i] UTC už importovaný: {p}")
        continue
    new = s.replace(
        "from datetime import datetime\n",
        "from datetime import UTC, datetime\n",
    )
    if new == s:
        print(f"[!] nenašiel 'from datetime import datetime' v {p} — skontroluj manuálne")
    else:
        open(p, "w").write(new)
        print(f"[x] UTC doplnený: {p}")
PY

echo
echo "--- kontrola ---"
grep -n "from datetime\|datetime.now(UTC)" \
  app/modules/inquiries/application/services.py \
  app/modules/listings/application/services.py

echo
echo "==============================================="
echo " 2. Znovu odstráň module_routers blok v main.py"
echo "==============================================="
python - <<'PY'
import re
p = "app/main.py"
src = open(p).read()

if "module_routers" not in src:
    print("[i] blok už nie je v main.py")
else:
    pattern = re.compile(
        r"\n    module_routers = \[.*?\n(?=    app\.state\.mounted_routers)",
        re.DOTALL,
    )
    new, n = pattern.subn("\n", src)
    print(f"[i] nájdených blokov: {n}")
    open(p, "w").write(new)
PY

echo
echo "--- kontrola ---"
grep -n "module_routers" app/main.py || echo "[ok] blok je preč"
echo -n "include_router count: "
grep -c "app.include_router" app/main.py

echo
echo "==============================================="
echo " 3. Rýchly pytest"
echo "==============================================="
pytest -q 2>&1 | tail -5

echo
echo "==============================================="
echo " 4. Pre-commit manuálne (ak je nainštalovaný)"
echo "==============================================="
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit run --all-files || echo "[!] pre-commit stále padá, pozri výstup vyššie"
else
  echo "[i] pre-commit nie je nainštalovaný"
fi

echo
echo "==============================================="
echo " 5. Commit"
echo "==============================================="
git add -A
git commit -m "Fix: remove duplicate router registration, add UTC to datetimes" || \
  echo "[!] commit zlyhal — najpravdepodobnejšie pre-commit. Pozri výstup."
git log --oneline -3
