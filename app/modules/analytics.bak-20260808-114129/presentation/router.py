"""analytics API router."""

from fastapi import APIRouter, HTTPException

from app.modules.analytics.presentation.schemas import (
    AnalyticsCreateRequest,
    AnalyticsUpdateRequest,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/")
async def list_analytics():
    raise HTTPException(status_code=501, detail="Analytics listing is not implemented")


@router.get("/{id}")
async def get_analytics(id: str):
    raise HTTPException(status_code=501, detail="Analytics detail is not implemented")


@router.post("/")
async def create_analytics(request: AnalyticsCreateRequest):
    raise HTTPException(status_code=501, detail="Analytics creation is not implemented")


@router.put("/{id}")
async def update_analytics(id: str, request: AnalyticsUpdateRequest):
    raise HTTPException(status_code=501, detail="Analytics update is not implemented")


@router.delete("/{id}")
async def delete_analytics(id: str):
    raise HTTPException(status_code=501, detail="Analytics deletion is not implemented")
