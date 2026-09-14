#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

echo "==============================================="
echo " 1. Záloha main.py"
echo "==============================================="
cp app/main.py app/main.py.bak
echo "[ok] app/main.py.bak"

echo
echo "==============================================="
echo " 2. Inicializácia mounted / skipped (ak chýba)"
echo "==============================================="
python - <<'PY'
import re
p = "app/main.py"
src = open(p).read()

# Nájdi, kde sa mounted a skipped používajú, ale nedefinujú
if "mounted = []" not in src and "mounted: list" not in src:
    # vlož ich pred "try:\n        from app.shared.presentation.api_router"
    src = src.replace(
        "    try:\n        from app.shared.presentation.api_router",
        "    mounted: list[str] = []\n    skipped: list[dict] = []\n\n    try:\n        from app.shared.presentation.api_router",
        1,
    )
    print("[x] pridaná inicializácia mounted/skipped")

open(p, "w").write(src)
PY

echo
echo "==============================================="
echo " 3. Odstráň duplicitný module_routers blok"
echo "==============================================="
python - <<'PY'
import re
p = "app/main.py"
src = open(p).read()

pattern = re.compile(
    r"\n    module_routers = \[.*?\n(?=    app\.state\.mounted_routers)",
    re.DOTALL,
)
new, n = pattern.subn("\n", src)
print(f"[i] nájdených blokov: {n}")
open(p, "w").write(new)
PY

echo
echo "==============================================="
echo " 4. Kontrola main.py (relevantná časť)"
echo "==============================================="
sed -n '55,120p' app/main.py

echo
echo "==============================================="
echo " 5. Over, že include_router pre moduly je len raz"
echo "==============================================="
grep -c "app.include_router" app/main.py

echo
echo "==============================================="
echo " 6. pytest"
echo "==============================================="
pytest -q
