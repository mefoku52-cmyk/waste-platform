"""Live voice token endpoint — generuje krátkodobý Deepgram token pre browser.

Frontend potom posiela mikrofón priamo do Deepgram streaming STT (nova-3);
prepis ide do existujúceho CMEP chatu, ktorý vráti text aj hlas (TTS).
Náš backend iba overí JWT + AI tier a vydá krátkodobý token.
"""

from __future__ import annotations

import contextlib
import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.presentation.chat_router import _check_ai_entitlement
from app.modules.agent_platform.presentation.dependencies import (
    get_company_entitlement_service,
)
from app.modules.companies.application.entitlements import CompanyEntitlementService
from app.shared.application.side_effects import write_audit
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-platform/voice", tags=["agent-platform-voice-live"])


@router.post("/token")
async def voice_token(
    current_user=Depends(require_current_user),
    entitlements: CompanyEntitlementService = Depends(get_company_entitlement_service),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Vygeneruj krátkodobý Deepgram access token pre live voice v prehliadači.

    Vyžaduje rovnaké oprávnenie ako AI chat: prihlásený user + PRO/AI tier.
    """
    await _check_ai_entitlement(current_user=current_user, entitlements=entitlements)

    key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="Hlasový asistent nie je nakonfigurovaný.",
        )

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.post(
                "https://api.deepgram.com/v1/auth/grant",
                headers={"Authorization": f"Token {key}"},
                json={"ttl_seconds": 60},
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.exception("Deepgram token request failed")
        raise HTTPException(
            status_code=502,
            detail="Hlasový asistent momentálne nie je dostupný.",
        ) from exc

    token = data.get("access_token")
    if not token:
        raise HTTPException(
            status_code=502,
            detail="Nepodarilo sa získať prístup k hlasovému asistentovi.",
        )

    expires_in = int(data.get("expires_in") or 60)

    # Rovnaká stopa ako ostatné AI cesty: kto, kedy a na čo dostal prístup.
    # Best-effort — audit nesmie zhodiť samotné hlasové spojenie.
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=current_user_id(current_user),
            action="agent.voice.token_granted",
            target_type="agent_voice_token",
            details=f"provider=deepgram,ttl_seconds={expires_in}",
        )

    return {
        "access_token": token,
        "expires_in": expires_in,
    }
