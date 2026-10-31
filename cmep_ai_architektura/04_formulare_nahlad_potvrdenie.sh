#!/data/data/com.termux/files/usr/bin/bash
set -u

REPO="$HOME/waste-platform"
BASE="$REPO/cmep_ai_architektura"
OUT="$BASE/vystupy"

mkdir -p "$OUT"

STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="$OUT/04_formulare_nahlad_potvrdenie_${STAMP}.txt"

if [ -e "$REPORT" ]; then
    echo "STOP: Vystup uz existuje: $REPORT"
    exit 1
fi

{
    echo "CMEP AI - DAVKA 04"
    echo "FORMULARE, NAHLAD A POTVRDENIE"
    echo "READ-ONLY AUDIT"
    echo "Datum: $(date)"
    echo

    if [ ! -d "$REPO/.git" ]; then
        echo "CHYBA: Repo nebolo najdene."
        exit 1
    fi

    cd "$REPO" || exit 1

    echo "=== 1. STAV REPOZITARA ==="
    git branch --show-current
    git rev-parse HEAD
    git status --short
    echo

    echo "=== 2. FRONTEND AI FORMULARE ==="
    for F in \
      apps/web/src/lib/ai-agent/use-ai-form-filling.ts \
      apps/web/src/lib/ai-agent/form-fields.ts \
      apps/web/src/lib/ai-agent/page-context.ts \
      apps/web/src/lib/ai-agent/dispatcher.ts \
      apps/web/src/features/agent-platform/components/ai-chat-widget.tsx
    do
        echo
        echo "--- $F ---"
        if [ -f "$F" ]; then
            grep -nE \
              'fill_form_field|highlight_field|setValue|handleSubmit|client_actions|dispatch|success|error|confirm|preview|submit|reset' \
              "$F" || true
        else
            echo "NEEXISTUJE"
        fi
    done

    echo
    echo "=== 3. FORMULAR PONUKY ==="
    find apps/web/src/features/listings \
      -type f \( -iname '*form*' -o -iname '*schema*' \) \
      -print 2>/dev/null | sort

    echo
    echo "=== 4. FORMULAR FIRMY ==="
    find apps/web/src/features/companies \
      -type f \( -iname '*form*' -o -iname '*schema*' \) \
      -print 2>/dev/null | sort

    echo
    echo "=== 5. OSTATNE FORMULARE ==="
    find apps/web/src/features \
      -type f \( -iname '*form*' -o -iname '*wizard*' \) \
      -print 2>/dev/null | sort | head -200

    echo
    echo "=== 6. POTVRDENIE A NAHLAD PRED ULOZENIM ==="
    grep -RniE \
      'preview|confirmation|confirm.*submit|submit.*confirm|review.*form|before.*submit|are you sure|potvrdiť|potvrdit|náhľad|nahlad' \
      apps/web/src \
      --include='*.ts' --include='*.tsx' \
      2>/dev/null | head -300 || true

    echo
    echo "=== 7. BACKEND ZAPISOVACIE ENDPOINTY ==="
    grep -RniE \
      'create_listing|update_listing|create_company|update_company|publish|submit' \
      app/modules/listings \
      app/modules/companies \
      --include='*.py' \
      2>/dev/null | head -300 || true

    echo
    echo "=== 8. TESTY FORMULAROV A AI VYPĹŇANIA ==="
    find apps/web app/modules/agent_platform/tests tests \
      -type f \
      \( -iname '*form*' -o -iname '*client_action*' -o -iname '*listing*' -o -iname '*company*' \) \
      2>/dev/null | sort | head -300

    echo
    echo "=== 9. ZAVERECNY STAV ==="
    git branch --show-current
    git rev-parse --short HEAD
    git status --short

    echo
    echo "KONIEC DAVKY 04"
    echo "Zdrojove subory neboli upravovane."
} 2>&1 | tee "$REPORT"

echo
echo "AUDITNY VYSTUP:"
echo "$REPORT"
echo "DAVKA 04 DOKONCENA"
