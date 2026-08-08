"""notifications API router."""

from fastapi import APIRouter, Depends
from typing import List

from .schemas import NotificationsResponse, NotificationsCreateRequest, NotificationsUpdateRequest
from ..application.services import NotificationsService
from ..infrastructure.repositories import NotificationsRepositoryImpl

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_service():
    """Get notifications service."""
    # TODO: Implement dependency injection
    pass


@router.get("/", response_model=List[NotificationsResponse])
async def list_notifications(page: int = 1, limit: int = 20):
    """List all notifications."""
    # TODO: Implement
    return []


@router.get("/{id}", response_model=NotificationsResponse)
async def get_notifications(id: str):
    """Get notifications by ID."""
    # TODO: Implement
    pass


@router.post("/", response_model=NotificationsResponse)
async def create_notifications(request: NotificationsCreateRequest):
    """Create new notifications."""
    # TODO: Implement
    pass


@router.put("/{id}", response_model=NotificationsResponse)
async def update_notifications(id: str, request: NotificationsUpdateRequest):
    """Update notifications."""
    # TODO: Implement
    pass


@router.delete("/{id}")
async def delete_notifications(id: str):
    """Delete notifications."""
    # TODO: Implement
    pass
