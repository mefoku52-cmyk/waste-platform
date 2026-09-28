#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd /data/data/com.termux/files/home/waste-platform
python3 -c 'from pathlib import Path; m=Path("app/modules/agent_platform"); need=["application/security/security_engine.py","infrastructure/security/security_event_store.py","application/alerts/alert_service.py","application/audit/audit_service.py"]; miss=[n for n in need if not (m/n).exists()];
raise SystemExit("MISSING "+",".join(miss)) if miss else print("SECURITY_EVENTS_OK")'
