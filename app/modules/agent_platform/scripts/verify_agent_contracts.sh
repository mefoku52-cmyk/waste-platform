#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd /data/data/com.termux/files/home/waste-platform
python3 -c 'from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway; from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest; from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse; assert hasattr(ModelGateway, "generate"); print("CONTRACTS_OK")'
