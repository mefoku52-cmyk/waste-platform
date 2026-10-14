#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/waste-platform"
OUT="$ROOT/cmep-ui-audit.txt"

cd "$ROOT" || exit 1

show_file() {
  FILE="$1"

  if [ -f "$FILE" ]; then
    echo
    echo "================================================================================"
    echo "FILE: $FILE"
    echo "================================================================================"
    sed -n '1,1400p' "$FILE"
  fi
}

{
  echo "CMEP UI AUDIT"
  echo "DATE: $(date)"
  echo "ROOT: $ROOT"

  echo
  echo "================================================================================"
  echo "GIT STATUS"
  echo "================================================================================"
  git status --short 2>&1 || true
  git branch --show-current 2>&1 || true
  git log -5 --oneline 2>&1 || true

  echo
  echo "================================================================================"
  echo "DIRECTORY TREE"
  echo "================================================================================"
  find apps/web/src -type f 2>/dev/null | sort || true

  echo
  echo "================================================================================"
  echo "PROJECT CONFIG"
  echo "================================================================================"
  show_file "package.json"
  show_file "apps/web/package.json"
  show_file "apps/web/src/app/layout.tsx"
  show_file "apps/web/src/app/page.tsx"
  show_file "apps/web/src/app/globals.css"
  show_file "apps/web/tailwind.config.ts"
  show_file "apps/web/tailwind.config.js"
  show_file "apps/web/tsconfig.json"

  echo
  echo "================================================================================"
  echo "ALL LAYOUT FILES"
  echo "================================================================================"
  find apps/web/src -type f -name 'layout.tsx' 2>/dev/null | sort | while IFS= read -r FILE; do
    show_file "$FILE"
  done

  echo
  echo "================================================================================"
  echo "ALL DASHBOARD FILES"
  echo "================================================================================"
  find apps/web/src/app/dashboard -type f 2>/dev/null | sort | while IFS= read -r FILE; do
    show_file "$FILE"
  done

  echo
  echo "================================================================================"
  echo "LISTING / OFFER / RECOMMENDATION FRONTEND FILES"
  echo "================================================================================"
  find apps/web/src -type f 2>/dev/null \
    | grep -E 'listing|listings|offer|offers|recommend|company|companies|inquir' \
    | grep -E '.tsx$|.ts$' \
    | sort \
    | while IFS= read -r FILE; do
        show_file "$FILE"
      done

  echo
  echo "================================================================================"
  echo "I18N / LOCALE FILES"
  echo "================================================================================"
  find apps/web/src -type f 2>/dev/null \
    | grep -E 'i18n|locale|locales|message|messages|translation|translations' \
    | sort \
    | while IFS= read -r FILE; do
        show_file "$FILE"
      done

  echo
  echo "================================================================================"
  echo "SEARCH: SCROLL / FIXED / STICKY / OVERFLOW"
  echo "================================================================================"
  grep -RInE 'h-screen|100vh|100dvh|overflow-hidden|overflow-y-auto|overflow-auto|sticky|fixed' \
    apps/web/src \
    --include='*.tsx' \
    --include='*.ts' \
    --include='*.css' \
    2>/dev/null || true

  echo
  echo "================================================================================"
  echo "SEARCH: TRC / CMEP / WELCOME"
  echo "================================================================================"
  grep -RInE 'TRČ|CMEP|C-MEP|Vitajte|vitajte|Welcome|welcome|добро' \
    apps/web/src \
    --include='*.tsx' \
    --include='*.ts' \
    --include='*.json' \
    2>/dev/null || true

  echo
  echo "================================================================================"
  echo "BACKEND LISTING / COMPANY / IMAGE / MEDIA FILES"
  echo "================================================================================"
  find app -type f 2>/dev/null \
    | grep -E 'listing|listings|offer|offers|company|companies|image|images|media|upload|file' \
    | grep -E '.py$' \
    | sort \
    | while IFS= read -r FILE; do
        show_file "$FILE"
      done

  echo
  echo "================================================================================"
  echo "BACKEND ROUTE SEARCH"
  echo "================================================================================"
  grep -RInE 'include_router|APIRouter|prefix=|listing|company|image|media|upload' \
    app \
    --include='*.py' \
    2>/dev/null || true

  echo
  echo "================================================================================"
  echo "END OF AUDIT"
  echo "================================================================================"
} > "$OUT"

echo "HOTOVO: $OUT"
wc -l "$OUT"
wc -c "$OUT"
