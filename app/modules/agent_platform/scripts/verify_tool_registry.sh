#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd /data/data/com.termux/files/home/waste-platform
python3 -c 'from pathlib import Path; p=Path("app/modules/agent_platform/infrastructure/tools"); need=["tool_catalog.py","forbidden_tool_names.py","safe_tool_registry.py","cmep_tool_dispatcher.py"]; miss=[n for n in need if not (p/n).exists()];
raise SystemExit("MISSING "+",".join(miss)) if miss else print("TOOL_REGISTRY_OK")'
