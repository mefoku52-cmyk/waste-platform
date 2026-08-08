"""inquiries API router."""

from fastapi import APIRouter, Depends
from typing import List

from .schemas import InquiriesResponse, InquiriesCreateRequest, InquiriesUpdateRequest
from ..application.services import InquiriesService
from ..infrastructure.repositories import InquiriesRepositoryImpl

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


def get_service():
    """Get inquiries service."""
    # TODO: Implement dependency injection
    pass


@router.get("/", response_model=List[InquiriesResponse])
async def list_inquiries(page: int = 1, limit: int = 20):
    """List all inquiries."""
    # TODO: Implement
    return []


@router.get("/{id}", response_model=InquiriesResponse)
async def get_inquiries(id: str):
    """Get inquiries by ID."""
    # TODO: Implement
    pass


@router.post("/", response_model=InquiriesResponse)
async def create_inquiries(request: InquiriesCreateRequest):
    """Create new inquiries."""
    # TODO: Implement
    pass


@router.put("/{id}", response_model=InquiriesResponse)
async def update_inquiries(id: str, request: InquiriesUpdateRequest):
    """Update inquiries."""
    # TODO: Implement
    pass


@router.delete("/{id}")
async def delete_inquiries(id: str):
    """Delete inquiries."""
    # TODO: Implement
    pass
