"""admin API router."""

from fastapi import APIRouter, HTTPException

from app.modules.admin.presentation.schemas import (
    AdminCreateRequest,
    AdminUpdateRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def list_admin():
    raise HTTPException(status_code=501, detail="Admin listing is not implemented")


@router.get("/{id}")
async def get_admin(id: str):
    raise HTTPException(status_code=501, detail="Admin detail is not implemented")


@router.post("/")
async def create_admin(request: AdminCreateRequest):
    raise HTTPException(status_code=501, detail="Admin creation is not implemented")


@router.put("/{id}")
async def update_admin(id: str, request: AdminUpdateRequest):
    raise HTTPException(status_code=501, detail="Admin update is not implemented")


@router.delete("/{id}")
async def delete_admin(id: str):
    raise HTTPException(status_code=501, detail="Admin deletion is not implemented")
