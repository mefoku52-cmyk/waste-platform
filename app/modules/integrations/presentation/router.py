import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/health")
async def integrations_health():
    return {"status": "available", "implementation": "partial"}


@router.get("/connections")
async def list_connections(
    current_user=Depends(require_current_user),
    db=Depends(get_db_session),
):
    # Zoznam sa nesmie vrátiť bez firemného rozsahu a databázovej implementácie.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Zoznam integrácií zatiaľ nie je implementovaný.",
    )


@router.post("/connections/test")
async def test_connection(
    current_user=Depends(require_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Test pripojenia vyžaduje konkrétny integračný adapter.",
    )


@router.post("/connections")
async def create_connection(
    current_user=Depends(require_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Vytváranie spojení čaká na databázovú a autorizačnú implementáciu.",
    )


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    current_user=Depends(require_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Odstránenie spojenia zatiaľ nie je implementované.",
    )


@router.post("/connections/{connection_id}/sync")
async def sync_connection(
    connection_id: str,
    current_user=Depends(require_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Synchronizácia vyžaduje adapter a plánovač úloh.",
    )
