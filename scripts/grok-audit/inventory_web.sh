#!/usr/bin/env bash
set -eu
OUT="${1:-$HOME/waste-platform/scripts/grok-audit/inventory_web.txt}"
{
  echo "===== META ====="
  echo "HEAD=$(git rev-parse --short HEAD)"
  echo

  echo "===== TREE ====="
  find apps/web -type d \( -name node_modules -o -name .next -o -name dist \) -prune -o -type d -print \
    | sed 's|^./||' | awk -F/ 'NF<=6' | sort | head -n 120
  echo

  echo "===== PAGES ====="
  find apps/web -type f \( -name 'page.tsx' -o -name 'page.jsx' -o -name 'layout.tsx' -o -name 'layout.jsx' \) \
    ! -path '*/node_modules/*' ! -path '*/.next/*' | sort
  echo

  echo "===== KEY FILES ====="
  for f in \
    apps/web/package.json \
    apps/web/app/layout.tsx \
    apps/web/app/page.tsx \
    apps/web/src/app/layout.tsx \
    apps/web/src/app/page.tsx \
    apps/web/app/globals.css \
    apps/web/src/app/globals.css
  do
    if [ -f "$f" ]; then
      echo "----- $f -----"
      wc -l "$f"
      sed -n '1,80p' "$f"
      echo
    fi
  done

  echo "===== LOGIN / DASHBOARD HITS ====="
  grep -RIl --include='*.tsx' --include='*.jsx' --include='*.css' \
    -E 'login|dashboard|listing|sponsor|advert|grant' apps/web \
    | grep -v node_modules | grep -v .next | head -n 40
  echo
  echo "===== END ====="
} > "$OUT"
echo "WROTE $OUT"
wc -c "$OUT"
