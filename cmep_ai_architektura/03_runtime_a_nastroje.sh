#!/data/data/com.termux/files/usr/bin/bash
set -u

REPO="$HOME/waste-platform"
BASE="$REPO/cmep_ai_architektura"
OUT="$BASE/vystupy"

if [ ! -d "$REPO/.git" ]; then
    echo "STOP: Repo nebolo najdene."
    exit 1
fi

mkdir -p "$OUT"
STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="$OUT/03_runtime_a_nastroje_$STAMP.txt"

cd "$REPO" || exit 1

{
    echo "CMEP AI - DAVKA 03"
    echo "RUNTIME A KATALOG NASTROJOV"
    echo "READ-ONLY AUDIT"
    echo "Datum: $(date)"

    echo
    echo "=== 1. STAV REPOZITARA ==="
    git branch --show-current
    git rev-parse HEAD
    git status --short --branch

    echo
    echo "=== 2. STRUKTURA TOOLS ==="
    find app/modules/agent_platform -type f \
      -path '*tools*' -name '*.py' -print 2>/dev/null | sort

    echo
    echo "=== 3. REGISTRACIA HANDLEROV ==="
    grep -RniE -C 3 \
      'register_tool|register_handler|tool_registry|ToolRegistry|handlers\[|\.register\(' \
      app/modules/agent_platform \
      --include='*.py' 2>/dev/null | head -700 || true

    echo
    echo "=== 4. TOOL EXECUTOR A DISPATCHER ==="
    grep -RniE \
      'class .*Executor|class .*Dispatcher|execute_tool|execute_call|dispatch_tool|call_tool|tool_handler' \
      app/modules/agent_platform \
      --include='*.py' 2>/dev/null || true

    echo
    echo "=== 5. TOOL CATALOG ==="
    F="app/modules/agent_platform/infrastructure/tools/tool_catalog.py"
    if [ -f "$F" ]; then
        sed -n '1,420p' "$F"
    fi

    echo
    echo "=== 6. TOOL SCHEMAS: ZOZNAM FUNKCII ==="
    F="app/modules/agent_platform/infrastructure/tools/tool_schemas.py"
    if [ -f "$F" ]; then
        grep -nE \
          '^[A-Z0-9_]+_SCHEMA|^def build_|"name":|"description":' \
          "$F" || true
    fi

    echo
    echo "=== 7. TOOL HANDLER ADAPTERS ==="
    F="app/modules/agent_platform/infrastructure/tools/handler_adapters.py"
    if [ -f "$F" ]; then
        sed -n '1,420p' "$F"
    else
        echo "NEEXISTUJE: $F"
    fi

    echo
    echo "=== 8. ZAPOJENIE DEPENDENCY INJECTION ==="
    F="app/modules/agent_platform/presentation/dependencies.py"
    if [ -f "$F" ]; then
        sed -n '1,340p' "$F"
    fi

    echo
    echo "=== 9. ORCHESTRATOR: REGISTRACIA A VOLANIE ==="
    F="app/modules/agent_platform/application/agent/agent_orchestrator.py"
    if [ -f "$F" ]; then
        grep -nE -C 5 \
          'tool_schemas|tool_handlers|handler|execute|validate|permission|policy|audit|tool_calls' \
          "$F" || true
    fi

    echo
    echo "=== 10. SERVEROVE A KLIENTSKE AKCIE ==="
    grep -RniE \
      'CLIENT_ACTION_NAMES|validate_client_action|ClientAction\(|tool_calls|client_actions' \
      app/modules/agent_platform \
      --include='*.py' 2>/dev/null | head -600 || true

    echo
    echo "=== 11. NAPOJENIE NA CMEP SLUZBY ==="
    grep -RniE \
      'ListingService|CompanyService|InquiryService|NotificationService|Transport|search_listings|search_companies|get_listing_transport' \
      app/modules/agent_platform \
      --include='*.py' 2>/dev/null | head -600 || true

    echo
    echo "=== 12. DUPLICITNE DEFINICIE A NAZVY NASTROJOV ==="
    grep -RhoE \
      '"name"[[:space:]]*:[[:space:]]*"[^"]+"' \
      app/modules/agent_platform \
      --include='*.py' 2>/dev/null | sort | uniq -c | sort -nr

    echo
    echo "=== 13. TESTY RUNTIME A NASTROJOV ==="
    find tests app/modules/agent_platform -type f \
      \( -iname '*tool*test*.py' -o -iname 'test*tool*.py' \
         -o -iname '*handler*test*.py' -o -iname 'test*handler*.py' \
         -o -iname '*catalog*test*.py' -o -iname 'test*catalog*.py' \) \
      -print 2>/dev/null | sort

    echo
    echo "=== 14. ZAVERECNY STAV ==="
    git branch --show-current
    git rev-parse --short HEAD
    git status --short

    echo
    echo "KONIEC DAVKY 03"
    echo "Zdrojove subory neboli upravovane."
} 2>&1 | tee "$REPORT"

echo
echo "AUDITNY VYSTUP: $REPORT"
echo "DAVKA 03 DOKONCENA"
