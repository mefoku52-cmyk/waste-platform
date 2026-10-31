#!/data/data/com.termux/files/usr/bin/bash
set -u

REPO="$HOME/waste-platform"
BASE="$REPO/cmep_ai_architektura"
OUT="$BASE/vystupy"

if [ ! -d "$REPO/.git" ]; then
    echo "STOP: Repo nebolo najdene."
    exit 1
fi

if [ -e "$BASE/05_bezpecnost_a_schvalovanie.sh" ]; then
    echo "STOP: Skript uz existuje. Nic neprepisujem."
    exit 1
fi

mkdir -p "$OUT"

STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="$OUT/05_bezpecnost_a_schvalovanie_${STAMP}.txt"

if [ -e "$REPORT" ]; then
    echo "STOP: Vystup uz existuje."
    exit 1
fi

cd "$REPO" || exit 1

{
    echo "CMEP AI - DAVKA 05"
    echo "BEZPECNOST, OPRAVNENIA A SCHVALOVANIE"
    echo "READ-ONLY AUDIT"
    echo "Datum: $(date)"
    echo

    echo "=== 1. STAV REPOZITARA ==="
    git branch --show-current
    git rev-parse HEAD
    git status --short
    echo

    echo "=== 2. BEZPECNOSTNE A SCHVALOVACIE SUBORY ==="
    find app/modules/agent_platform \
      -type f \
      \( -iname '*policy*' -o -iname '*permission*' -o -iname '*approval*' \
         -o -iname '*gate*' -o -iname '*security*' -o -iname '*scope*' \) \
      ! -path '*/__pycache__/*' \
      -print 2>/dev/null | sort

    echo
    echo "=== 3. EXECUTION POLICY ==="
    for F in \
      app/modules/agent_platform/application/execution_policy.py \
      app/modules/agent_platform/application/agent_gate.py \
      app/modules/agent_platform/application/approval_workflow.py \
      app/modules/agent_platform/application/default_approval_workflow.py
    do
        if [ -f "$F" ]; then
            echo
            echo "--- $F ---"
            grep -nE \
              'class |def |async def |DISABLED|DRY_RUN|APPROVED|allow|deny|block|approval|pending|execute|completed|audit|write|delete|deploy|migrate|shell|commit|push' \
              "$F" || true
        fi
    done

    echo
    echo "=== 4. SCHVALOVACIE ROUTY ==="
    find app/modules/agent_platform \
      -type f -iname '*approval*' \
      ! -path '*/__pycache__/*' \
      -print 2>/dev/null | while IFS= read -r F; do
          echo
          echo "--- $F ---"
          grep -nE \
            'router|@.*post|@.*get|approve|reject|pending|status|user|admin|permission|audit|execute' \
            "$F" || true
      done

    echo
    echo "=== 5. POLICY A OPRAVNENIA V RUNTIME ==="
    grep -RniE \
      'policy\.|permission\.|request_approval|requires_approval|approval_workflow|tool_scopes|check_permission|authorize|is_admin|is_platform_admin' \
      app/modules/agent_platform \
      --include='*.py' \
      --exclude-dir='__pycache__' \
      2>/dev/null | head -400 || true

    echo
    echo "=== 6. ZAPISOVACIE A RIZIKOVE OPERACIE ==="
    grep -RniE \
      'shell_exec|file_write|file_delete|db_write|db_migrate|git_commit|git_push|deploy|install|delete|publish|create_listing|update_listing|create_company|update_company' \
      app/modules/agent_platform \
      --include='*.py' \
      --exclude-dir='__pycache__' \
      2>/dev/null | head -400 || true

    echo
    echo "=== 7. SCHVALOVACIE TESTY ==="
    find app/modules/agent_platform tests \
      -type f \
      \( -iname '*approval*' -o -iname '*policy*' -o -iname '*permission*' \
         -o -iname '*execution*' -o -iname '*agent_gate*' \) \
      ! -path '*/__pycache__/*' \
      -print 2>/dev/null | sort

    echo
    echo "=== 8. TESTOVACIE ASSERTY SCHVALOVANIA ==="
    grep -RniE \
      'requires_approval|request_approval|pending_approval|APPROVED|DRY_RUN|DISABLED|approval|unauthorized|forbidden|permission' \
      app/modules/agent_platform/tests tests \
      --include='test_*.py' \
      --exclude-dir='__pycache__' \
      2>/dev/null | head -400 || true

    echo
    echo "=== 9. INTEGRACIA SCHVALOVANIA S CHAT ROUTAMI ==="
    for F in \
      app/modules/agent_platform/presentation/chat_router.py \
      app/modules/agent_platform/presentation/user_ai_chat_router.py \
      app/modules/agent_platform/application/agent/agent_orchestrator.py \
      app/modules/agent_platform/presentation/dependencies.py
    do
        if [ -f "$F" ]; then
            echo
            echo "--- $F ---"
            grep -nE \
              'approval|requires_approval|request_approval|policy|permission|execute|tool_handler|client_actions|tool_calls' \
              "$F" || true
        fi
    done

    echo
    echo "=== 10. ZAVERECNY STAV ==="
    git branch --show-current
    git rev-parse --short HEAD
    git status --short

    echo
    echo "KONIEC DAVKY 05"
    echo "Zdrojove subory neboli upravovane."
} 2>&1 | tee "$REPORT"

echo
echo "AUDITNY VYSTUP:"
echo "$REPORT"
echo "DAVKA 05 DOKONCENA"
