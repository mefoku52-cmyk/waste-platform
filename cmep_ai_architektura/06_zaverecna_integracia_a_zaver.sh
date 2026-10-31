#!/data/data/com.termux/files/usr/bin/bash
set -u

BASE="$HOME/waste-platform/cmep_ai_architektura"
REPO="$HOME/waste-platform"
OUT="$BASE/vystupy"

if [ -e "$BASE/06_zaverecna_integracia_a_zaver.sh" ]; then
    echo "STOP: Skript uz existuje. Nic neprepisujem."
    exit 1
fi

mkdir -p "$OUT" || exit 1
REPORT="$OUT/06_zaverecna_integracia_$(date +%Y%m%d_%H%M%S).txt"

exec > >(tee "$REPORT") 2>&1

section() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

show_file() {
    local file="$1"
    local pattern="$2"

    echo
    echo "--- $file ---"

    if [ -f "$REPO/$file" ]; then
        grep -nE "$pattern" "$REPO/$file" || true
    else
        echo "SUBOR NEEXISTUJE"
    fi
}

section "CMEP AI - DAVKA 06"
echo "ZAVERECNA INTEGRACNA KONTROLA"
echo "READ-ONLY AUDIT"
date
echo "Repo: $REPO"

section "1. GIT STAV"
git -C "$REPO" branch --show-current
git -C "$REPO" rev-parse HEAD
git -C "$REPO" status --short

section "2. CHAT ROUTY A ORCHESTRATOR"

show_file "app/modules/agent_platform/presentation/chat_router.py" \
    'get_agent_orchestrator|AgentOrchestrator|tool_calls|client_actions|arguments|nav_tool_calls|approval|approval_workflow'

show_file "app/modules/agent_platform/presentation/user_ai_chat_router.py" \
    'get_agent_orchestrator|AgentOrchestrator|tool_calls|client_actions|arguments|nav_tool_calls|approval|approval_workflow'

show_file "app/modules/agent_platform/application/agent/agent_orchestrator.py" \
    'MAX_TOOL_ITERATIONS|policy\.decide|permission\.authorize|requires_approval|tool_handlers|get\(tool_name\)|dispatched_to_client|executed'

section "3. SCHVALOVACIA INTEGRACIA"

show_file "app/modules/agent_platform/application/pipeline/agent_pipeline.py" \
    'approval|create|awaiting_approval|execute|dispatch'

show_file "app/modules/agent_platform/application/approval/approval_workflow.py" \
    'class |async def |APPROVED|PENDING|create|execute|approval'

show_file "app/modules/agent_platform/presentation/approvals_router.py" \
    '@router\.|require_admin|approve|deny|is-executable|approval_workflow'

show_file "app/modules/agent_platform/presentation/dependencies.py" \
    'get_approval|ApprovalWorkflow|ApprovalService|AgentOrchestrator|tool_handlers|policy|permission'

section "4. EXECUTION POLICY A RIZIKOVE OPERACIE"

show_file "app/modules/agent_platform/navigator/execution_policy.py" \
    'class ExecutionMode|FORBIDDEN|ALLOWED|def execute|def request_approval|APPROVED|completed|executed'

show_file "app/modules/agent_platform/navigator/task_coordinator.py" \
    'def run|ExecutionMode|is_allowed|execute|approval|authorize'

section "5. FRONTENDOVE AKCIE"

show_file "apps/web/src/lib/ai-agent/dispatcher.ts" \
    'register|dispatch|no_handler|handler|subscribe'

show_file "apps/web/src/features/ai/hooks/use-ai-form-filling.ts" \
    'fill_form_field|highlight_field|setValue|register'

show_file "apps/web/src/features/ai/components/ai-chat-widget.tsx" \
    'dispatch|fill_form_field|open_|router\.push|success|error'

section "6. TESTY INTEGRACIE"

find "$REPO/app/modules/agent_platform/tests" \
     "$REPO/tests" \
     -type f \( -name '*approval*.py' -o -name '*pipeline*.py' -o -name '*orchestrator*.py' -o -name '*chat*.py' -o -name '*client_action*.py' \) \
     -not -path '*/node_modules/*' \
     -not -path '*/.venv/*' \
     -print 2>/dev/null | sort

section "7. VYHLADANIE PRIAMYCH VAZIEB SCHVALOVANIA"

grep -RInE \
    'get_approval_workflow|DefaultApprovalWorkflow|create_request|awaiting_approval|requires_approval_policy|requires_approval_permission' \
    "$REPO/app/modules/agent_platform/presentation" \
    "$REPO/app/modules/agent_platform/application" \
    --include='*.py' \
    --exclude-dir='__pycache__' \
    2>/dev/null || true

section "8. ZAVERECNY GIT STAV"

git -C "$REPO" branch --show-current
git -C "$REPO" rev-parse --short HEAD
git -C "$REPO" status --short

echo
echo "KONIEC DAVKY 06"
echo "Zdrojove subory neboli upravovane."
echo "AUDITNY VYSTUP:"
echo "$REPORT"
echo "DAVKA 06 DOKONCENA"
