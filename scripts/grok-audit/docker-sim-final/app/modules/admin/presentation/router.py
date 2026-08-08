"""admin API router."""

from fastapi import APIRouter, Depends
from typing import List

from .schemas import AdminResponse, AdminCreateRequest, AdminUpdateRequest
from ..application.services import AdminService
from ..infrastructure.repositories import AdminRepositoryImpl

router = APIRouter(prefix="/admin", tags=["admin"])


def get_service():
    """Get admin service."""
    # TODO: Implement dependency injection
    pass


@router.get("/", response_model=List[AdminResponse])
async def list_admin(page: int = 1, limit: int = 20):
    """List all admin."""
    # TODO: Implement
    return []


@router.get("/{id}", response_model=AdminResponse)
async def get_admin(id: str):
    """Get admin by ID."""
    # TODO: Implement
    pass


@router.post("/", response_model=AdminResponse)
async def create_admin(request: AdminCreateRequest):
    """Create new admin."""
    # TODO: Implement
    pass


@router.put("/{id}", response_model=AdminResponse)
async def update_admin(id: str, request: AdminUpdateRequest):
    """Update admin."""
    # TODO: Implement
    pass


@router.delete("/{id}")
async def delete_admin(id: str):
    """Delete admin."""
    # TODO: Implement
    pass
