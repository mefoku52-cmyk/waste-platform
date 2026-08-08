"""listings API router."""

from fastapi import APIRouter, Depends
from typing import List

from .schemas import ListingsResponse, ListingsCreateRequest, ListingsUpdateRequest
from ..application.services import ListingsService
from ..infrastructure.repositories import ListingsRepositoryImpl

router = APIRouter(prefix="/listings", tags=["listings"])


def get_service():
    """Get listings service."""
    # TODO: Implement dependency injection
    pass


@router.get("/", response_model=List[ListingsResponse])
async def list_listings(page: int = 1, limit: int = 20):
    """List all listings."""
    # TODO: Implement
    return []


@router.get("/{id}", response_model=ListingsResponse)
async def get_listings(id: str):
    """Get listings by ID."""
    # TODO: Implement
    pass


@router.post("/", response_model=ListingsResponse)
async def create_listings(request: ListingsCreateRequest):
    """Create new listings."""
    # TODO: Implement
    pass


@router.put("/{id}", response_model=ListingsResponse)
async def update_listings(id: str, request: ListingsUpdateRequest):
    """Update listings."""
    # TODO: Implement
    pass


@router.delete("/{id}")
async def delete_listings(id: str):
    """Delete listings."""
    # TODO: Implement
    pass
