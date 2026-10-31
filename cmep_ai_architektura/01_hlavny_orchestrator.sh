#!/data/data/com.termux/files/usr/bin/bash
set -u

REPO="$HOME/waste-platform"

echo "CMEP AI - DAVKA 01"
echo "HLAVNY ORCHESTRATOR"
echo "READ-ONLY AUDIT"

if [ ! -d "$REPO/.git" ]; then
    echo "CHYBA: Repo nebolo najdene."
    exit 1
fi

cd "$REPO" || exit 1

echo
echo "=== REPOSITORY STAV ==="
git branch --show-current
git rev-parse HEAD
git status --short --branch

echo
echo "=== EXISTUJUCE AI MODULY ==="
find app/modules/agent_platform \
  -maxdepth 4 -type f -name '*.py' \
  -print 2>/dev/null | sort

echo
echo "=== HLAVNY ORCHESTRATOR ==="
F="app/modules/agent_platform/application/agent/agent_orchestrator.py"
if [ -f "$F" ]; then
    sed -n '1,420p' "$F"
else
    echo "NEEXISTUJE: $F"
fi

echo
echo "=== CHAT ROUTER ==="
F="app/modules/agent_platform/presentation/chat_router.py"
if [ -f "$F" ]; then
    grep -nE \
      'navigator|orchestrator|respond|tool_calls|client_actions|validate|approval|permission|policy' \
      "$F" || true
else
    echo "NEEXISTUJE: $F"
fi

echo
echo "=== NAVIGATOR BRIDGE ==="
F="app/modules/agent_platform/navigator/navigator_bridge.py"
if [ -f "$F" ]; then
    sed -n '1,360p' "$F"
else
    echo "NEEXISTUJE: $F"
fi

echo
echo "=== MODEL GATEWAY A PROVIDERI ==="
find app/modules/agent_platform \
  -type f \
  \( -iname '*gateway*.py' -o -iname '*adapter*.py' -o -iname '*provider*.py' \) \
  -print 2>/dev/null | sort

echo
echo "=== DEPENDENCY INJECTION ==="
grep -RniE \
  'AgentOrchestrator|ChainModelGateway|build_default_model_chain|GenericAPIAdapter|FallbackAdapter' \
  app/modules/agent_platform \
  --include='*.py' 2>/dev/null || true

echo
echo "=== TOOL SCHEMAS A VALIDACIA ==="
for F in \
  app/modules/agent_platform/infrastructure/tools/tool_schemas.py \
  app/modules/agent_platform/infrastructure/tools/client_action_validation.py \
  app/modules/agent_platform/infrastructure/tools/tool_catalog.py
do
    echo
    echo "--- $F ---"
    if [ -f "$F" ]; then
        sed -n '1,320p' "$F"
    else
        echo "NEEXISTUJE"
    fi
done

echo
echo "=== TESTY ORCHESTRATORA ==="
find tests -type f \
  \( -iname '*agent*' -o -iname '*orchestrat*' \) \
  -print 2>/dev/null | sort | head -200

echo
echo "=== ZHRNUTIE ==="
git branch --show-current
git rev-parse --short HEAD
git status --short

echo
echo "KONIEC DAVKY 01"
echo "Bez zmien v repozitari."
