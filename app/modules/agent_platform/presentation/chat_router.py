from __future__ import annotations

import asyncio
import contextlib
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.application.agent.intent_classifier import (
    IntentResult,
    classify_intent,
    intent_hint,
)
from app.modules.agent_platform.application.memory.context_builder import build_history
from app.modules.agent_platform.domain.control.agent_gate import (
    AgentGate,
    resolve_agent_gate,
)
from app.modules.agent_platform.domain.control.control_mode import ControlMode
from app.modules.agent_platform.infrastructure.ai.voice_gateway import synthesize_with_edge_tts
from app.modules.agent_platform.infrastructure.persistence.ai_conversation_repository import (
    SqlAlchemyAiConversationRepository,
)
from app.modules.agent_platform.infrastructure.tools.tool_schemas import CLIENT_ACTION_NAMES
from app.modules.agent_platform.presentation.dependencies import (
    get_agent_orchestrator,
    get_ai_conversation_repository,
    get_company_entitlement_service,
    get_control_service,
)
from app.modules.companies.application.entitlements import CompanyEntitlementService
from app.modules.companies.domain.enums import SubscriptionTier
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_platform_admin,
    membership_company_ids,
)

router = APIRouter(prefix="/agent-platform", tags=["agent-platform"])
