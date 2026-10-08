from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.modules.agent_platform.infrastructure.ai.voice_gateway import (
    AZURE_MAX_AUDIO_BYTES,
    transcribe_with_mai,
)
from app.modules.agent_platform.presentation.chat_router import _check_ai_entitlement
from app.modules.agent_platform.presentation.dependencies import get_company_entitlement_service
from app.modules.companies.application.entitlements import CompanyEntitlementService
from app.shared.presentation.auth_dependencies import require_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-platform/voice", tags=["agent-platform-voice"])


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user=Depends(require_current_user),
    entitlements: CompanyEntitlementService = Depends(get_company_entitlement_service),
) -> dict[str, str | None]:
    # Same logged-in user and AI subscription entitlement as the existing chat.
    await _check_ai_entitlement(current_user=current_user, entitlements=entitlements)
    content_type = (audio.content_type or "").lower()
    if not (
        content_type.startswith("audio/")
        or content_type in {"application/octet-stream", "video/webm"}
    ):
        raise HTTPException(status_code=415, detail="Nepodporovaný audio formát.")
    content = await audio.read(AZURE_MAX_AUDIO_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Nahrávka je prázdna.")
    if len(content) > AZURE_MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Nahrávka je príliš veľká (limit 15 MB).")
    try:
        return await transcribe_with_mai(
            content,
            audio.filename or "recording.webm",
            content_type or "audio/webm",
        )
    except Exception as exc:
        logger.exception("Voice transcription provider request failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502, detail="Prepis hlasu sa nepodaril. Skús to znova."
        ) from exc
