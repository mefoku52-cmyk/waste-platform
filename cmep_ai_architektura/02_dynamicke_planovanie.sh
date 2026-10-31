#!/data/data/com.termux/files/usr/bin/bash
set -u

REPO="$HOME/waste-platform"
BASE="$REPO/cmep_ai_architektura"
OUT="$BASE/vystupy"

if [ ! -d "$REPO/.git" ]; then
    echo "STOP: Repo nebolo najdene: $REPO"
    exit 1
fi

mkdir -p "$OUT"

if [ -e "$BASE/02_dynamicke_planovanie.sh" ]; then
    echo "STOP: Skript uz existuje. Nic neprepisujem."
    exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="$OUT/02_dynamicke_planovanie_$STAMP.txt"

cd "$REPO" || exit 1

{
    echo "CMEP AI - DAVKA 02"
    echo "DYNAMICKÉ PLANOVANIE A VYKONAVANIE ULOH"
    echo "READ-ONLY AUDIT"
    echo "Datum: $(date)"
    echo "Repo: $REPO"

    echo
    echo "=== 1. STAV REPOZITARA ==="
    git branch --show-current
    git rev-parse HEAD
    git status --short --branch

    echo
    echo "=== 2. VYHLADANIE PLANOVACICH MODULOV ==="
    find app/modules/agent_platform \
      -type f -name '*.py' \
      \( -iname '*task*' -o -iname '*plan*' -o -iname '*coordinat*' \
         -o -iname '*execution*' -o -iname '*role*' \) \
      -print 2>/dev/null | sort

    echo
    echo "=== 3. TASK INTAKE ==="
    find app/modules/agent_platform -type f \
      \( -name 'task_intake.py' -o -name '*intake*.py' \) \
      -print 2>/dev/null |
    while IFS= read -r F; do
        echo
        echo "--- $F ---"
        sed -n '1,360p' "$F"
    done

    echo
    echo "=== 4. TASK COORDINATOR ==="
    find app/modules/agent_platform -type f \
      \( -name 'task_coordinator.py' -o -name '*coordinator*.py' \) \
      -print 2>/dev/null |
    while IFS= read -r F; do
        echo
        echo "--- $F ---"
        sed -n '1,420p' "$F"
    done

    echo
    echo "=== 5. EXECUTION POLICY ==="
    find app/modules/agent_platform -type f \
      \( -name 'execution_policy.py' -o -name '*policy*.py' \) \
      -print 2>/dev/null |
    while IFS= read -r F; do
        echo
        echo "--- $F ---"
        sed -n '1,360p' "$F"
    done

    echo
    echo "=== 6. ROLE MANAGER A AGENT ROLE ==="
    grep -RniE \
      'class AgentRoleManager|class AgentRole|register_agent|assign_agent|COORDINATOR|WORKER' \
      app/modules/agent_platform \
      --include='*.py' 2>/dev/null || true

    echo
    echo "=== 7. NAVIGATOR: PLANOVANIE A VYKONAVANIE ==="
    F="app/modules/agent_platform/navigator/navigator_bridge.py"
    if [ -f "$F" ]; then
        grep -nE \
          'TaskIntake|TaskCoordinator|\.accept\(|\.run\(|assignment|tasks|tool_calls|arguments|action|infer\(' \
          "$F" || true
    else
        echo "NEEXISTUJE: $F"
    fi

    echo
    echo "=== 8. CHAT ROUTER: PREPOJENIE PLANU ==="
    for F in \
      app/modules/agent_platform/presentation/chat_router.py \
      app/modules/agent_platform/presentation/user_ai_chat_router.py
    do
        echo
        echo "--- $F ---"
        if [ -f "$F" ]; then
            grep -nE -C 5 \
              'navigator|TaskCoordinator|task_coordinator|tool_calls|client_actions|arguments|old_orchestrator|respond\(' \
              "$F" || true
        else
            echo "NEEXISTUJE"
        fi
    done

    echo
    echo "=== 9. ORCHESTRATOR: ITERACIE A VYSLEDKY NASTROJOV ==="
    F="app/modules/agent_platform/application/agent/agent_orchestrator.py"
    if [ -f "$F" ]; then
        grep -nE -C 4 \
          'MAX_TOOL_ITERATIONS|tool_calls|tool_results|tool_choice|execute|handler|iteration|gateway|messages' \
          "$F" || true
    else
        echo "NEEXISTUJE: $F"
    fi

    echo
    echo "=== 10. VSETKY VYUZITIA TASK COORDINATORA ==="
    grep -RniE \
      'TaskCoordinator|\.run\(.*task|coordinator\.run|_coordinator\.run' \
      app tests \
      --include='*.py' 2>/dev/null || true

    echo
    echo "=== 11. TESTY PLANOVANIA A VYKONAVANIA ==="
    find tests app/modules/agent_platform -type f \
      \( -iname '*task*test*.py' -o -iname 'test*task*.py' \
         -o -iname '*coordinator*test*.py' -o -iname 'test*coordinator*.py' \
         -o -iname '*execution*test*.py' -o -iname 'test*execution*.py' \
         -o -iname '*navigator*test*.py' -o -iname 'test*navigator*.py' \) \
      -print 2>/dev/null | sort

    echo
    echo "=== 12. TESTY: KLUCOVE ASSERTIONS ==="
    grep -RniE \
      'assert.*(task|plan|retry|timeout|attempt|dependency|approval)|TaskCoordinator|TaskIntake|ExecutionPolicy' \
      tests app/modules/agent_platform \
      --include='test_*.py' 2>/dev/null | head -400 || true

    echo
    echo "=== 13. KONFIGURACIA CASOV A OPAKOVANIA ==="
    grep -RniE \
      'max_attempts|default_timeout|timeout=|retry|backoff|MAX_TOOL_ITERATIONS|ExecutionMode' \
      app/modules/agent_platform \
      --include='*.py' 2>/dev/null | head -300 || true

    echo
    echo "=== 14. ZAVERECNY STAV ==="
    git branch --show-current
    git rev-parse --short HEAD
    git status --short

    echo
    echo "KONIEC DAVKY 02"
    echo "Repo zdrojove subory neboli upravovane."
} 2>&1 | tee "$REPORT"

echo
echo "AUDITNY VYSTUP:"
echo "$REPORT"
echo "DAVKA 02 DOKONCENA"
