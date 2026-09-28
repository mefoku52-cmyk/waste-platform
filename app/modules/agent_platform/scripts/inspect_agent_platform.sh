#!/usr/bin/env bash
set -euo pipefail
ROOT="\( (cd " \)(dirname "$0")/../../.." && pwd)"
MOD="$ROOT/app/modules/agent_platform"
echo "AGENT_PLATFORM $MOD"
echo "py $(find "$MOD" -name '*.py' ! -name '*.backup*' | wc -l)"
echo "chat_router $([ -f "$MOD/presentation/chat_router.py" ] && echo OK || echo MISSING)"
echo "control_router $([ -f "$MOD/presentation/control_router.py" ] && echo OK || echo MISSING)"
echo "groq $([ -f "$MOD/infrastructure/ai/groq_gateway.py" ] && echo OK || echo MISSING)"
