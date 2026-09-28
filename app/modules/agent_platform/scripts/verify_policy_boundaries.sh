#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd /data/data/com.termux/files/home/waste-platform
python3 -c 'from pathlib import Path; m=Path("app/modules/agent_platform"); need=["application/policy/policy_engine.py","application/permission/permission_engine.py","application/approval/approval_service.py"]; miss=[n for n in need if not (m/n).exists()];
raise SystemExit("MISSING "+",".join(miss)) if miss else print("POLICY_BOUNDARIES_OK")'
