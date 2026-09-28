#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd /data/data/com.termux/files/home/waste-platform
MOD=app/modules/agent_platform
echo AGENT_PLATFORM "$PWD/$MOD"
echo py "$(find "$MOD" -name '*.py' ! -name '*.backup*' | wc -l)"
test -f "$MOD/presentation/chat_router.py" && echo chat_router OK || echo chat_router MISSING
test -f "$MOD/presentation/control_router.py" && echo control_router OK || echo control_router MISSING
test -f "$MOD/infrastructure/ai/groq_gateway.py" && echo groq OK || echo groq MISSING
