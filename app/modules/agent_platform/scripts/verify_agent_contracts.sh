#!/usr/bin/env bash
set -euo pipefail
ROOT="\( (cd " \)(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse
assert hasattr(ModelGateway, "generate")
assert "request_id" in ModelRequest.__dataclass_fields__
assert "text" in ModelResponse.__dataclass_fields__
print("CONTRACTS_OK")
PY
